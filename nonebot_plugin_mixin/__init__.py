"""
通过 mixin 调整特定 Matcher 的行为

注意：本插件并不保证更改会被稳定应用，部分插件可能会在运行时修改自身部分行为。
"""

from functools import partial, reduce
import json
from operator import and_
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, Union
from nonebot import get_driver, logger
from nonebot.internal.matcher import Matcher, matchers
from nonebot.internal.rule import Rule
from nonebot.rule import (
    StartswithRule, EndswithRule, FullmatchRule,
    KeywordsRule, CommandRule, RegexRule, ToMeRule,
    command
)
from pydantic import BaseModel, Field

from .config import Config

global_config = get_driver().config
config_ = Config.parse_obj(global_config)

driver = get_driver()


class CaseMatch(BaseModel):
    msg: Tuple[str, ...]
    ignorecase: bool = False


class ReMatch(BaseModel):
    regex: str
    flags: int = 0


class MixinRule(BaseModel):
    startswith: Optional[CaseMatch] = None
    endswith: Optional[CaseMatch] = None
    fullmatch: Optional[CaseMatch] = None
    keywords: Optional[Tuple[str, ...]] = None
    command: Optional[Tuple[Tuple[str, ...]]] = None
    regex: Optional[ReMatch] = None
    to_me: bool = False

    def __contains__(self, subrule: "MixinRule") -> bool:
        cmdcond, recond, tomecond = True, True, True
        if self.command is not None:
            cmdcond = (
                set(tuple(cmd) for cmd in subrule.command or ())
                <= set(tuple(cmd) for cmd in self.command)
            )
        if self.regex is not None:
            recond = (
                True if subrule.regex is None else self.regex == subrule.regex
            )
        elif subrule.regex is not None:
            recond = False
        tomecond = self.to_me == subrule.to_me
        return cmdcond and recond and tomecond and all(
            set(getattr(subrule, x) or ()) <= set(getattr(self, x) or ())
            for x in ("startswith", "endswith", "fullmatch", "keywords")
        )

    @classmethod
    def from_rule(cls, rule: Rule):
        kwds = {}
        for sub in rule.checkers:
            sr = sub.call
            if isinstance(sr, StartswithRule):
                kwds["startswith"] = CaseMatch(msg=sr.msg, ignorecase=sr.ignorecase)
            elif isinstance(sr, EndswithRule):
                kwds["endswith"] = CaseMatch(msg=sr.msg, ignorecase=sr.ignorecase)
            elif isinstance(sr, FullmatchRule):
                kwds["fullmatch"] = CaseMatch(msg=sr.msg, ignorecase=sr.ignorecase)
            elif isinstance(sr, KeywordsRule):
                kwds["keywords"] = sr.keywords
            elif isinstance(sr, CommandRule):
                kwds["command"] = sr.cmds
            elif isinstance(sr, RegexRule):
                kwds["regex"] = ReMatch(regex=sr.regex, flags=sr.flags)
            elif isinstance(sr, ToMeRule):
                kwds["to_me"] = True
        return cls(**kwds)

    @classmethod
    def from_matcher(cls, matcher: Type[Matcher]):
        return cls.from_rule(matcher.rule)

    def to_rule(self, parent: Optional[Rule] = None):
        rule = Rule()
        tmp = []
        complex_rules = zip(
            (self.startswith, self.endswith, self.fullmatch, self.regex),
            (StartswithRule, EndswithRule, FullmatchRule, RegexRule)
        )
        if parent is not None:
            for sub in parent.checkers:
                if not isinstance(
                    sub.call,
                    (
                        StartswithRule, EndswithRule, FullmatchRule,
                        KeywordsRule, CommandRule, RegexRule, ToMeRule,
                    )
                ):
                    rule.checkers.add(sub)
                    continue
                tmp.append(sub.call)
        for loc, obj in complex_rules:
            if loc is not None:
                rule &= obj(**loc.dict())
            else:
                rule: Rule = reduce(
                    and_, filter(lambda x: isinstance(x, obj), tmp), rule
                )
        if self.keywords is not None:
            rule &= KeywordsRule(*self.keywords)
        else:
            rule: Rule = reduce(
                and_, filter(lambda x: isinstance(x, KeywordsRule), tmp), rule
            )
        if self.command is not None:
            rule &= command(*self.command)
        else:
            rule: Rule = reduce(
                and_, filter(lambda x: isinstance(x, CommandRule), tmp), rule
            )
        if self.to_me:
            rule &= ToMeRule()
        return rule


class MixinQuery(BaseModel):
    plugin_name: Optional[str] = None
    module_name: Optional[str] = None
    type: Optional[str] = None
    rule: MixinRule = Field(default_factory=MixinRule)
    priority: Optional[int] = None
    block: Optional[bool] = None

    def __contains__(self, ma: Type[Matcher]):
        return self.rule in MixinRule.from_matcher(ma) and all(
            getattr(ma, x) == getattr(self, x)
            for x in (
                "plugin_name", "module_name", "type", "priority", "block"
            ) if getattr(self, x) is not None
        )


class MixinData(BaseModel):
    type: Optional[str] = None
    rule: MixinRule = Field(default_factory=MixinRule)
    priority: Optional[int] = None
    block: Optional[bool] = None


class Mixin(BaseModel):
    source: MixinQuery
    dest: MixinData


mixins: List[Mixin] = []


def mixin(ma: Type[Matcher], ch: MixinData):
    if ch.type is not None:
        ma.type = ch.type
    ma.rule = ch.rule.to_rule(ma.rule)
    if ch.priority is not None:
        # This operation only changes the priority in the matcher, which
        # means another place the priority stored in should also be changed.
        ma.priority = ch.priority
    if ch.block is not None:
        ma.block = ch.block
    logger.info(f"已介入 {ma!r} 的属性")


def update_priority(ma: Type[Matcher], before: int, after: int):
    if before not in matchers or ma not in matchers[before]:
        logger.warning(
            f"{ma!r} 不在给定的旧优先级 {before} 中，"
            f"无法移至新优先级 {after} 组"
        )
        return
    if before == after:
        logger.info("优先级未变化，不进行移动")
        return
    matchers[after] = matchers.get(after, []) + [ma]
    matchers[before].remove(ma)
    logger.info(f"已移动 {ma!r} 的优先级 ({before} -> {after})")
    if not matchers[before]:
        del matchers[before]
        logger.debug("已移除旧优先级的空槽位")


def multi_mixin(mixin_: Iterable[Mixin] = mixins):
    move = []
    for pri, mas in matchers.items():
        matched = [
            x for x in mixin_
            if x.source.priority is None
            or x.source.priority == pri
        ]
        if not any(matched):
            logger.debug(f"优先级 {pri} 没有可用的 Mixin")
            continue
        for ma in mas:
            for pair in matched:
                if ma not in pair.source:
                    logger.debug(f"{pair!r} 未命中 {ma!r}")
                    continue
                mixin(ma, pair.dest)
                if (prio := pair.dest.priority) is not None:
                    move.append(partial(update_priority, ma, pri, prio))
                break
    for f in move:
        f()


def read_mixin(*files: Union[str, Path]) -> Iterable[List[Any]]:
    paths = (Path(file) for file in files)
    for fp in paths:
        if not fp.is_file():
            logger.warning(f"{fp!r} 不是一个文件")
            continue
        if fp.suffix == ".json":
            with open(fp) as f:
                yield json.load(f)
        else:
            logger.warning(f"尚未支持 {fp!r} 的数据格式")
    return


def parse_mixin(*rules: Any):
    for r in rules:
        mixins.append(Mixin.parse_obj(r))


@driver.on_startup
async def load_mixin_files():
    for obj in read_mixin(*config_.mixin_source):
        parse_mixin(*obj)
    multi_mixin()