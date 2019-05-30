#!/usr/bin/env python
# coding=utf-8


import os
import sys
import unittest

root = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(os.path.join(root, "src"))
import lexex


class LexexUnittests(unittest.TestCase):

    def setUp(self):
        self.lexex = lexex.Lexex(os.path.join(root, "rules/toycase.rule"))

    def test_sample_match(self):

        """ 支持最简单的匹配抽取
        """

        word_array = [u"我", u"是", u"诸", u"葛", u"亮"]
        label_array = [u"o", u"o", u"B", u"M", u"E"]
        match = self.lexex.match(word_array, label_array, 0)
        res = match.match_collection
        self.assertEqual(' '.join(res['entity']), u'诸葛亮')

    def test_match_next(self):

        """ 对match进行迭代抽取，可以枚举出全部匹配结果
        """

        word_array = [u"我", u"是", u"诸", u"葛", u"亮", u"，", u"你", u"是", u"李", u"白"]
        label_array = [u"o", u"o", u"B", u"M", u"E", u"o", u"o", u"o", u"B", u"E"]
        match = self.lexex.match(word_array, label_array, 0)
        res = match.match_collection
        self.assertEqual(' '.join(res['entity']), u'诸葛亮')
        match = match.get_next()
        res = match.match_collection
        self.assertEqual(' '.join(res['entity']), u'李白')

    @unittest.expectedFailure
    def test_unsame_rules(self):
        word_array = [u"铠", u"和", u"诸", u"葛", u"亮"]
        label_array = [u"S", u"o", u"B", u"M", u"E"]
        match = self.lexex.match(word_array, label_array, 0)
        res = match.match_collection
        self.assertEqual(' '.join(res['entity']), u'铠')
        match = match.get_next()
        res = match.match_collection
        self.assertEqual(' '.join(res['entity']), u'诸葛亮')

    def test_unsame_rules2(self):

        """ 使用枚举方法可以
        """

        word_array = [u"诸", u"葛", u"亮", u"和", u"铠"]
        label_array = [u"B", u"M", u"E", u"o", u"S"]
        match = self.lexex.match(word_array, label_array, 0)
        res = match.match_collection
        self.assertEqual(' '.join(res['entity']), u'诸葛亮')
        match = match.get_next()
        res = match.match_collection
        self.assertEqual(' '.join(res['entity']), u'铠')

    def test_star(self):

        """ 贪婪匹配，例如：使用越过项+通配符可以直接匹配到整句全部
        """

        word_array = [u"老", u"人", u"与", u"海"]
        label_array = [u"B", u"M", u"M", u"E"]
        lex = lexex.Lexex(os.path.join(root, "rules/star.rule"))
        match = lex.match(word_array, label_array, 0)
        res = match.match_collection
        self.assertEqual(' '.join(res['res']), u'老人与海')


if __name__ == "__main__":
    unittest.main()
