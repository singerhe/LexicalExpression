#!/usr/bin/env python
# coding=utf-8


import os
import sys
reload(sys)
sys.setdefaultencoding("utf8")


class LexicalExpressionMatcher(object):

    def __init__(self, rule):
        self.__rule = rule
        self.match_values = []
        self.current_match_value = {}

    def try_match(self, word_array, label_array, start_index, match):

        if not isinstance(match, Match):
            raise Exception("match must be a Match() instance.")

        if len(word_array) != len(label_array):
            raise Exception("array lens error.")
        length = len(word_array)

        self.match_values = []
        self.current_match_value = {}

        word_position = start_index
        while word_position < length:

            if self._match_one_rule_for_sentence(0, word_array, label_array, word_position):
                self.current_match_value = dict(sorted(self.current_match_value.items(), key=lambda x: x[0]))
                self.match_values.append(self.current_match_value)
                last_match_index = -1
                for dic_pos in range(len(self.current_match_value) - 1, -1, -1):
                    last_match_index = self.current_match_value[dic_pos][1]
                    if last_match_index != -1:
                        break
                word_position = last_match_index + 1
                self.current_match_value = {}
            else:
                word_position += 1

        if self.match_values:

            match.word_array = word_array
            match.label_array = label_array
            match.match_rule = self.__rule
            match.match_values = self.match_values[0]
            match.begin_index = match.match_values[0][0]
            match.end_index = match.match_values[len(match.match_values)-1][1]
            match_res = {}
            match_value = self._get_match_lex_sentence(word_array, label_array, self.match_values[0])
            for right_rule_item in self.__rule.rule_right.right_rule_item_array:
                name = right_rule_item.name
                if not name:
                    for nameid in right_rule_item.name_id_list:
                        name += match_value[nameid - 1]
                name_builder = ""
                for id in right_rule_item.ids:
                    name_builder += ''.join(match_value[id - 1][0])
                if name in match_res:
                    match_res[name].append(name_builder)
                else:
                    match_res[name] = [name_builder]
            match.match_collection = match_res

            return 1
        else:
            self.current_match_value = {}
            return 0

    def _match_one_rule_for_sentence(self, start_rule_id, word_array, label_array, start_position):
        is_match = False

        ## 递归匹配结束条件。规则的全部节点都已经匹配成功。所以返回 true
        if start_rule_id >= len(self.__rule.rule_left.rule_item_array):
            return 1

        ## 递归匹配结束条件。已经匹配到句子末尾，但还有规则项未匹配，所以返回 false
        if start_position >= len(word_array):
            return 0

        rule_item = self.__rule.rule_left.rule_item_array[start_rule_id]

        ## 当期待匹配的规则项
        if rule_item.rule_kind == Constants.basic_rule_item:
            ## 基本项
            if rule_item.match(word_array, label_array, start_position) != -1:
                self.current_match_value[start_rule_id] = [start_position, start_position]
                return self._match_one_rule_for_sentence(start_rule_id+1, word_array, label_array, start_position+1)
            else:
                return 0
        elif rule_item.rule_kind == Constants.skip_rule_item:
            skip_rule_item = rule_item.rule_item
            low = skip_rule_item.low
            high = skip_rule_item.high

            if low == 1 and high == 1:
                # 越过项只有一项
                if skip_rule_item.match(word_array, label_array, start_position) != -1:
                    self.current_match_value[start_rule_id] = [start_position, start_position]
                    return self._match_one_rule_for_sentence(start_rule_id + 1, word_array, label_array,
                                                         start_position + 1)
                else:
                    return 0
            elif high >= low:
                # 越过项多于一项
                num_items_can_skiped = 0
                while num_items_can_skiped < high and num_items_can_skiped < len(word_array):
                    if skip_rule_item.match(word_array, label_array, start_position+num_items_can_skiped) in [-1, start_position + num_items_can_skiped]:
                        break
                    num_items_can_skiped += 1

                if num_items_can_skiped < low:
                    return 0

                is_match = False
                num_real_skiped = low
                while num_real_skiped <= num_items_can_skiped:
                    tmp = len(self.__rule.rule_left.rule_item_array) - 1
                    if start_rule_id == tmp and \
                        skip_rule_item.match(word_array, label_array, start_position + num_real_skiped) not in [-1, start_position + num_real_skiped]:
                        is_match = True
                        num_real_skiped += 1
                    else:
                        if self._match_one_rule_for_sentence(start_rule_id + 1, word_array, label_array, start_position + num_real_skiped):
                            is_match = True
                            break
                        else:
                            num_real_skiped += 1

                if is_match:
                    if num_real_skiped == 0:
                        self.current_match_value[start_rule_id] = [-1, -1]
                    else:
                        if start_rule_id == len(self.__rule.rule_left.rule_item_array) - 1:#and (start_position + num_real_skiped == len(word_array)):
                            self.current_match_value[start_rule_id] = [start_position, start_position + num_real_skiped]
                        else:
                            self.current_match_value[start_rule_id] = [start_position, start_position + num_real_skiped - 1]
                return is_match
            return 0
        else:
            return 0

    def _get_match_lex_sentence(self, word_array, label_array, cur_match_value):
        match_value = {}
        for key, value in cur_match_value.items():
            start = value[0]
            if start == -1:
                match_value[key] = ([""], [""])
                continue
            end = value[1]
            match_value[key] = (word_array[start:end + 1], label_array[start:end + 1])
        match_value = dict(sorted(match_value.items(), key=lambda x: x[0]))
        return match_value


class Rule(object):

    def __init__(self, rule_left = None, rule_right = None):
        self.rule_left = rule_left
        self.rule_right = rule_right

    def create_matcher(self):
        return LexicalExpressionMatcher(self)


## RuleRight.

class RuleRight(object):

    def __init__(self, right_rule_item_array=None):
        self.right_rule_item_array = right_rule_item_array


class RightRuleItem(object):

    def __init__(self):
        self.ids = []
        self.name = ""
        self.right_rule_kind = ""
        self.name_id_list = []


## RuleLeft.

class RuleLeft(object):

    def __init__(self):
        self.rule_item_array = []


class IRuleItem(object):

    def is_match(self, word, label, is_begin, is_end):
        pass

    def match(self, word_array, label_array, start_index):
        pass

    def to_string(self):
        pass


class RuleItem(IRuleItem):

    def __init__(self, rule_kind, rule_item):
        self.rule_kind = rule_kind
        self.rule_item = rule_item

    def is_match(self, word, label, is_begin, is_end):
        return self.rule_item.is_match(word, label, is_begin, is_end)

    def match(self, word_array, label_array, start_index):
        return self.rule_item.match(word_array, label_array, start_index)

    def to_string(self):
        return self.rule_item.to_string()


class BasicRuleItem(IRuleItem):

    def __init__(self, word_group, label_group):
        self.word_group = word_group
        self.label_group = label_group

    def is_match(self, word, label, is_begin, is_end):
        flag = self.word_group.is_match(word)
        if not flag:
            return 0
        flag = self.label_group.is_match(label, is_begin, is_end)
        return flag

    def match(self, word_array, label_array, start_index):
        if start_index < 0 or start_index > len(word_array) - 1:
            return -1
        word = word_array[start_index]
        label = label_array[start_index]
        is_begin = 1 if start_index == 0 else 0
        is_end = 1 if start_index == (len(word_array) - 1) else 0

        if self.is_match(word, label, is_begin, is_end):
            return start_index + 1
        else:
            return -1

    def to_string(self):
        return "[BasicRuleItem]: {}, {}".format(self.word_group.to_string(), self.label_group.to_string())

class SkipRuleItem(IRuleItem):

    def __init__(self, low, high, basic_rule_item):
        self.low = low
        self.high = high
        self.basic_rule_item = basic_rule_item

    def is_match(self, word, label, is_begin, is_end):
        if not self.basic_rule_item:
            return 1
        else:
            return self.basic_rule_item.is_match(word, label, is_begin, is_end)

    def match(self, word_array, label_array, start_index):

        if start_index < 0 or start_index > len(word_array) - 1:
            return -1

        if start_index + self.low > len(word_array) - 1:
            return -1

        is_begin = 1 if start_index == 0 else 0
        is_end = 1 if start_index == (len(word_array) - 1) else 0

        step = 0
        while step < self.low:
            if self.basic_rule_item.is_match(word_array[start_index + step], label_array[start_index + step], is_begin, is_end):
                step += 1
            else:
                return -1
        start_index = start_index + self.low

        while (start_index < len(word_array) - 1) and self.is_match(word_array[start_index], label_array[start_index], is_begin, is_end):
            start_index += 1
        return start_index

    def to_string(self):
        output = "[SkipRuleItem]: "
        output += "{}:{} ".format(self.low, self.high)
        output += self.basic_rule_item.to_string()
        return output

## Word Group.

class IWordMatching(object):

    def is_match(self, word):
        pass

    def to_string(self):
        pass


class WordGroup(IWordMatching):
    def __init__(self, is_star, word_expr):
        self.is_star = is_star
        self.word_expr = word_expr

    def is_match(self, word):
        if self.is_star:
            return 1
        return self.word_expr.is_match(word)

    def to_string(self):
        if self.is_star:
            return "[WordGroup]: *"
        else:
            return "[WordGroup]: {{{}}}".format(self.word_expr.to_string())


class WordExpression(IWordMatching):
    def __init__(self, word_item_array):
        self.word_item_array = word_item_array

    def is_match(self, word):
        flag = 0
        for word_item in self.word_item_array:
            if word_item.is_match(word):
                flag = 1
                break
        return flag

    def to_string(self):
        return "[WordExpression]: [{}]".format("".join([wi.to_string() for wi in self.word_item_array]))


class WordItem(IWordMatching):
    def __init__(self, word_kind, not_flag, word_atom, word_expr):
        self.word_kind = word_kind
        self.not_flag = not_flag
        self.word_atom = word_atom
        self.word_expr = word_expr

    def is_match(self, word):
        flag = False
        if self.word_kind == Constants.is_word_atom:
            flag = self.word_atom.is_match(word)
        else:
            flag = self.word_expr.is_match(word)
        return not flag if self.not_flag else flag

    def to_string(self):
        output = "[WordItem]:"
        if self.word_kind == Constants.is_word_atom:
            output += self.word_atom.to_string()
        else:
            if self.not_flag:
                output += "!{{{}}}".format(self.word_expr.to_string())
            else:
                output += "({{{}}})".format(self.word_expr.to_string())
        return output


class WordAtom(IWordMatching):
    def __init__(self, word):
        self.word = word

    def is_match(self, word):
        if not word:
            return 0
        return self.word == word

    def to_string(self):
        return "[WordAtom]: <{}>".format(self.word)


## Label Group.

class ILabelMatching(object):
    def is_match(self, label, is_start, is_end):
        pass

    def to_string(self):
        pass


class LabelGroup(ILabelMatching):
    def __init__(self, is_percent, label_expr):
        self.is_percent = is_percent
        self.label_expr = label_expr

    def is_match(self, label, is_start, is_end):
        if self.is_percent:
            return 1
        return self.label_expr.is_match(label, is_start, is_end)

    def to_string(self):
        if self.is_percent:
            return "[LabelGroup]: {{%}}"
        else:
            return "[LabelGroup]: {{{}}}".format(self.label_expr.to_string())


class LabelExpression(ILabelMatching):
    def __init__(self, label_item_array):
        self.label_item_array = label_item_array

    def is_match(self, label, is_start, is_end):
        flag = 0
        for label_item in self.label_item_array:
            if label_item.is_match(label, is_start, is_end):
                flag = 1
                break
        return flag

    def to_string(self):
        return "[LabelExpression]: [{}]".format("".join([le.to_string() for le in self.label_item_array]))


class LabelItem(ILabelMatching):
    def __init__(self, label_atom_array):
        self.label_atom_array = label_atom_array

    def is_match(self, label, is_start, is_end):
        flag = 1
        for label_atom in self.label_atom_array:
            if not label_atom.is_match(label, is_start, is_end):
                flag = 0
                break
        return flag

    def to_string(self):
        return "[LabelItem]: {}".format("".join([la.to_string() for la in self.label_atom_array]))


class LabelAtom(ILabelMatching):
    def __init__(self, label_kind, not_flag, label, label_expr):
        self.label_kind = label_kind
        self.not_flag = not_flag
        self.label_str = label
        self.label_expr = label_expr


    def is_match(self, label, is_start, is_end):
        flag = False
        if self.label_kind == Constants.is_label_str:
            if self.label_str == "^":
                if is_start:
                    flag = True
                else:
                    flag = False
            elif self.label_str == "$":
                if is_end:
                    flag = True
                else:
                    flag = False
            else:
                if self.label_str == label:
                    flag = True
                else:
                    flag = False
        else:
            flag = self.label_expr.is_match(label, is_start, is_end)
        return not flag if self.not_flag else flag

    def to_string(self):
        output = "[LabelAtom]: "
        if self.label_kind == 0:
            output += "<{}>".format(self.label_str)
        else:
            if self.not_flag:
                output += "!({})".format(self.label_expr.to_string())
            else:
                output += "({})".format(self.label_expr.to_string())
        return output


## RuleLoader.

class RuleLoader(object):

    def __init__(self):
        self.__current_rule = None
        self.__lex = None
        self.__token = None
        self.__lexval = None
        self.__chpos = None

    def load_rule(self, rule_str):
        self.__current_rule = rule_str + "\n\n"
        self.__chpos = 0
        self._get_token()

        rule = Rule()
        rule.rule_left = self._load_rule_left()
        if self.__token != Constants.equal:
            return None
        self._get_token()
        rule.rule_right = self._load_rule_right()
        return rule

    def _load_rule_left(self):
        rule_left = RuleLeft()
        i = 0
        item = self._load_rule_item()
        item.id = i
        i += 1
        rule_left.rule_item_array.append(item)
        while self.__token == Constants.plus:
            self._get_token()
            item = self._load_rule_item()
            item.id = i
            i += 1
            rule_left.rule_item_array.append(item)
        return rule_left

    def _load_rule_item(self):
        if self.__token == Constants.hashtag:
            rule_item = self._load_skip_item()
            item = RuleItem(Constants.skip_rule_item, rule_item)
        elif self.__token == Constants.lbrace:
            rule_item = self._load_option_item()
            item = RuleItem(Constants.option_rule_item, rule_item)
        else:
            rule_item = self._load_basic_item()
            item = RuleItem(Constants.basic_rule_item, rule_item)
        return item

    def _load_basic_item(self):
        word_group = self._load_word_group()
        if self.__token != Constants.slash:
            return None
        self._get_token()
        label_group = self._load_label_group()
        basic_item = BasicRuleItem(word_group, label_group)
        return basic_item

    def _load_skip_item(self):
        basic_item = None
        self._get_token()
        if self.__token != Constants.number:
            low = 0
            high = 65000
        else:
            low = self.lexval
            high = 65000
            self._get_token()
            if self.__token == Constants.colon:
                self._get_token()
                if self.__token != Constants.number:
                    return None
                high = self.lexval
                self._get_token()

        if self.__token == Constants.lbracket:
            self._get_token()
            basic_item = self._load_basic_item()
            if self.__token != Constants.rbracket:
                return None
            else:
                self._get_token()

        skip_item = SkipRuleItem(low, high, basic_item)
        return skip_item

    def _load_word_group(self):
        word_group = WordGroup(True, None)
        if self.__token != Constants.star:
            word_group.is_star = False
            word_group.word_expr = self._load_word_expression()
        else:
            self._get_token()
        return word_group

    def _load_word_expression(self):
        word_item_array = []
        word_item = self._load_word_item()
        word_item_array.append(word_item)

        while self.__token == Constants._or:
            self._get_token()
            word_item = self._load_word_item()
            word_item_array.append(word_item)

        word_expression = WordExpression(word_item_array)
        return word_expression

    def _load_word_item(self):
        if self.__token == Constants._not:
            self._get_token()
            word_expression = self._load_word_expression()
            word_item = WordItem(Constants.is_word_expr, True, None, word_expression)
        elif self.__token == Constants.lparen:
            self._get_token()
            word_expression = self._load_word_expression()
            if self.__token != Constants.rparen:
                return None
            self._get_token()
            word_item = WordItem(Constants.is_word_expr, False, None, word_expression)
        else:
            word_atom = self._load_word_atom()
            word_item = WordItem(Constants.is_word_atom, False, word_atom, None)
        return word_item

    def _load_word_atom(self):
        lex = ""
        while self.__token in [Constants.eng, Constants.hz, Constants.number]:
            lex += self.lex
            self._get_token()
        word_atom = WordAtom(lex)
        return word_atom

    def _load_label_group(self):
        label_group = LabelGroup(True, None)
        if self.__token != Constants.percent:
            label_group.is_percent = False
            label_group.label_expr = self._load_label_expression()
        else:
            self._get_token()
        return label_group

    def _load_label_expression(self):
        label_item_array = []
        label_item = self._load_label_item()
        label_item_array.append(label_item)
        while self.__token == Constants._or:
            self._get_token()
            label_item = self._load_label_item()
            label_item_array.append(label_item)
        label_expression = LabelExpression(label_item_array)
        return label_expression

    def _load_label_item(self):
        label_atom_array = []
        label_atom = self._load_label_atom()
        label_atom_array.append(label_atom)

        while self.__token == Constants._and:
            self._get_token()
            label_atom = self._load_label_atom()
            label_atom_array.append(label_atom)

        label_item = LabelItem(label_atom_array)
        return label_item

    def _load_label_atom(self):
        if self.__token == Constants._not:
            self._get_token()
            label_expr = self._load_label_expression()
            label_atom = LabelAtom(Constants.is_label_expr, True, None, label_expr)
        elif self.__token == Constants.lparen:
            self._get_token()
            label_expr = self._load_label_expression()
            if self.__token != Constants.rparen:
                return None
            label_atom = LabelAtom(Constants.is_label_expr, False, None, label_expr)
            self._get_token()
        else:
            if self.__token in [Constants.eng, Constants.number, Constants.mark, Constants.dollar]:
                label_atom = LabelAtom(Constants.is_label_str, False, self.lex, None)
                self._get_token()
            else:
                return None
        return label_atom

    def _load_rule_right(self):
        if self.__token == Constants.end:
            return None
        right_rule_item_array = []
        if self.__token == Constants.lbrace:
            right_rule_item = self._load_right_rule_item()
            right_rule_item_array.append(right_rule_item)
            while self.__token == Constants.plus:
                self._get_token()
                right_rule_item = self._load_right_rule_item()
                right_rule_item_array.append(right_rule_item)

            rule_right = RuleRight(right_rule_item_array)
            return rule_right
        else:
            return None

    def _load_right_rule_item(self):
        right_rule_item = RightRuleItem()
        if self.__token == Constants.lbrace:
            self._get_token()
            if self.__token in [Constants.eng or Constants.hz]:
                right_rule_item.name = self.lex
                self._get_token()
                if self.__token == Constants.colon:
                    self._get_token()
                else:
                    return None
                while self.__token == Constants.number:
                    right_rule_item.ids.append(int(self.lex))
                    self._get_token()
                    if self.__token == Constants.comma:
                        self._get_token()
                    else:
                        if self.__token == Constants.rbrace:
                            self._get_token()
                            return right_rule_item
                        return None
            elif self.__token == Constants.number:
                while self.__token == Constants.number:
                    right_rule_item.name_id_list.append(int(self.lex))
                    self._get_token()
                    if self.__token == Constants.comma:
                        self._get_token()
                    else:
                        break
                if self.__token == Constants.colon:
                    self._get_token()
                else:
                    return None
                while self.__token == Constants.number:
                    right_rule_item.ids.append(int(self.lex))
                    self._get_token()
                    if self.__token == Constants.comma:
                        self._get_token()
                    else:
                        if self.__token == Constants.rbrace:
                            self._get_token()
                            return right_rule_item
                        else:
                            return None
            else:
                return None
        else:
            return None
        return right_rule_item


    def _get_token(self):

        next = 0

        while self.__current_rule[self.__chpos] in [" ", "\t"]:
            self.__chpos += 1

        if self.__current_rule[self.__chpos] == "\n":
            self.__token = Constants.end
            return
        elif ord(self.__current_rule[self.__chpos]) > 256:
            self.__token = Constants.hz
            next = self.__chpos + 1
            while ord(self.__current_rule[next]) > 256:
                next += 1
            self.lex = self.__current_rule[self.__chpos: next]
            self.__chpos = next
            return
        elif self.__current_rule[self.__chpos] == '"':
            self.__token = Constants.eng
            next = self.__chpos + 1
            while self.__current_rule[next] != '"' and next < len(self.__current_rule):
                next += 1
            self.lex = self.__current_rule[self.__chpos + 1: next - 1]
            self.__chpos = next + 1
            return
        elif self.__current_rule[self.__chpos].isalpha():
            self.__token = Constants.eng
            next = self.__chpos + 1
            while self.__current_rule[next].isalpha():
                next += 1
            self.lex = self.__current_rule[self.__chpos: next]
            self.__chpos = next
            return
        elif self.__current_rule[self.__chpos].isdigit():
            self.__token = Constants.number
            next = self.__chpos + 1
            while self.__current_rule[next].isdigit():
                next += 1
            self.lex = self.__current_rule[self.__chpos: next]
            self.lexval = int(self.lex)
            self.__chpos = next
            return
        elif self.__current_rule[self.__chpos] == "^":
            self.__token = Constants.mark
            self.lex = "^"
            self.__chpos += 1
            return
        elif self.__current_rule[self.__chpos] == "$":
            self.__token = Constants.dollar
            self.lex = "$"
            self.__chpos += 1
        elif self.__current_rule[self.__chpos] == "#":
            if self.__current_rule[self.__chpos + 1] == "L":
                self.lex = "#L"
                self.__token = Constants.lhash
                self.__chpos += 2
                return
            elif self.__current_rule[self.__chpos + 1] == "R":
                self.lex = "#R"
                self.__token = Constants.rhash
                self.__chpos += 2
                return
            else:
                self.lex = "#"
                self.__token = Constants.hashtag
                self.__chpos += 1
                return
        else:
            self.lex = self.__current_rule[self.__chpos: self.__chpos + 1]
            tmp = self.__current_rule[self.__chpos]
            if tmp == "*": self.__token = Constants.star
            elif tmp == "%": self.__token = Constants.percent
            elif tmp == "/": self.__token = Constants.slash
            elif tmp == "=": self.__token = Constants.equal
            elif tmp == "+": self.__token = Constants.plus
            elif tmp == "|": self.__token = Constants._or
            elif tmp == "&": self.__token = Constants._and
            elif tmp == "!": self.__token = Constants._not
            elif tmp == "(": self.__token = Constants.lparen
            elif tmp == ")": self.__token = Constants.rparen
            elif tmp == "[": self.__token = Constants.lbracket
            elif tmp == "]": self.__token = Constants.rbracket
            elif tmp == "{": self.__token = Constants.lbrace
            elif tmp == "}": self.__token = Constants.rbrace
            elif tmp == ":": self.__token = Constants.colon
            elif tmp == "@": self.__token = Constants.address
            elif tmp == "-": self.__token = Constants.minus
            elif tmp == ",": self.__token = Constants.comma
            elif tmp == ";": self.__token = Constants.eng
            elif tmp == " ": self.__token = Constants.space
            elif tmp == "$": self.__token = Constants.dollar
            else: self.__token = Constants.error
            self.__chpos += 1
            return


## Constants.

class Constants(object):

    error = -1
    end = 0
    hz = 1
    eng = 2
    number = 3

    star = 4  # *
    percent = 5  # %
    slash = 6  # /
    equal = 7  # =
    plus = 8  # +
    _or = 9  # |
    _and = 10  # &
    _not = 11  # !
    lparen = 12  # (
    rparen = 13  # )
    lbracket = 14  # [
    rbracket = 15  # ]
    lbrace = 16  # {
    rbrace = 17  # }
    hashtag = 18  # #
    lhash = 19  # #L
    rhash = 20  # #R
    colon = 21  # :
    address = 22  # @
    minus = 23  # -
    space = 24  #
    mark = 25  # ^
    dollar = 26  # $
    comma = 27  # ,

    basic_rule_item = 1
    skip_rule_item = 2
    option_rule_item = 3
    left_hash_rule_item = 4
    right_hash_rule_item = 5
    start_pos_rule_item = 6
    end_pos_rule_item = 7

    is_word_expr = 1
    is_word_atom = 0

    is_label_expr = 1
    is_label_str = 0

    forward = True
    backward = False


class Match(object):

    def __init__(self):
        self.__lexex = None
        self.word_array = None
        self.label_array = None
        self.begin_index = -1
        self.end_index = -1
        self.match_rule = None
        self.match_values = None
        self.match_collection = {}

    def set_lexex(self, lexex):
        self.__lexex = lexex

    def get_next(self):
        return self.__lexex.match(self.word_array, self.label_array, self.end_index + 1)

    def __iter__(self):
        return iter(self.match_collection.items())


class Lexex(object):

    __loader = RuleLoader()

    def __init__(self, rule_path):

        self.__rules = []
        self._load_rules(rule_path)

    def _load_rules(self, rule_path):
        if not os.path.exists(rule_path):
            raise Exception("can not find rule file.")

        with open(rule_path, "r") as reader:
            for line in reader:
                rule = self.__loader.load_rule(unicode(line.strip()))
                if not rule:
                    continue
                self.__rules.append(rule)

    def rules_count(self):
        return len(self.__rules)

    def match(self, word_array, label_array, start_index):

        match = Match()
        for rule in self.__rules:
            matcher = rule.create_matcher()
            if matcher.try_match(word_array, label_array, start_index, match):
                match.set_lexex(self)
                return match
        return match


if __name__ == "__main__":

    lexex = Lexex("toycase.rule")
    print "\nload %s rules.\n" % (lexex.rules_count(),)

    words = [u"我要", u"听", u"科技", u"新闻"]
    labels = [u"stp", u"stp", u"cate", u"nws"]
    res = lexex.match(words, labels, 0)
    for key, value in res:
        print key
        print "key: %s      \t value: %s" % (key, str(' '.join(value)))
