# -*- coding: utf8 -*-
"""
docutils term validation extension

:copyright: Copyright 2011 by Takayuki SHIMIZUKAWA.
:license: Apache Software License 2.0
"""

__docformat__ = 'reStructuredText'

import io
import os
import re
import unicodedata
from functools import partial

from docutils.utils import column_width
from docutils import nodes

from sphinx import addnodes
from sphinx.ext.todo import todo_node

BASEDIR = os.path.dirname(os.path.abspath(__file__))

NG_WORDS = []


def validate_half_width_katakana(text, warn=lambda t:None):
    """
    If text include half-width-katakana, emit warning.

    :param unicode text: string to validate.
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    text2 = []
    for t in text:
        if unicodedata.category(t)[0] in ('L', 'N'):
            text2.append(unicodedata.normalize('NFKC', t))
        else:
            text2.append(t)

    text2 = ''.join(text2)
    if text != text2:
        warn(u'Wide ascii, Wide number or Half kana are found\n%s' % text)

    return text2


def validate_parenthesis(text, warn=lambda t:None):
    """
    If text include half parenthesis within wide text, emit warning.

    :param unicode text: string to validate.
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    text2 = text

    for term in re.findall(u'\(([^)]*)\)', text2):
        if column_width(term) != len(term):
            text2 = text2.replace(u'(%s)' % term, u'（%s）' % term)
            warn(u'Half parenthesis include Wide string\n%s' % term)

    return text2


def validate_question_exclamation(text, warn=lambda t:None):
    """
    If text include half question or exclamatoin, emit warning.

    :param unicode text: string to validate.
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    text2 = text

    if column_width(text2) != len(text2):
        for base, mark in re.findall(u'([ぁ-んァ-ヶー一-龠]+)([!?]+)', text2):
            wide_mark = mark.replace(u'!', u'！').replace(u'?', u'？')
            text2 = text2.replace(base + mark, base + wide_mark)

    if text != text2:
        warn(u'Half "!", "?" after full-width char is found\n%s' % text)

    return text2


def validate_punctuation_mark(text, warn=lambda t:None):
    """
    If text include ascii punctuation mark (.,) emit warning.

    :param unicode text: string to validate.
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    if not text:
        return text

    if column_width(text) == len(text):
        return text

    text2 = text

    # replace . with 。
    text2 = re.sub('[^\d,.]\. ',  u'。',   text2)  # ドット+スペース
    text2 = re.sub('[^\d,.]\.\n', u'。\n', text2)  # ドット+改行
    text2 = re.sub('[^\d,.]\.$',  u'。',   text2)  # ドット+終端
    # replace , with 、
    text2 = re.sub('[^,.], ',  u'、',   text2)  # カンマ+スペース
    text2 = re.sub('[^,.],\n', u'、\n', text2)  # カンマ+改行
    text2 = re.sub('[^,.],$',  u'、',   text2)  # カンマ+終端

    if text != text2:
        warn(u'ASCII punctuation mark are found\n%s' % text)

    return text2


def validate_space_in_number_of_unit(text, warn=lambda t:None):
    """
    If text did not include space in number of unit as "12 Mbps", emit warning.

    :param unicode text: string to validate.
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    if not text:
        return text

    text2 = text

    # need insert space at NUMBER+UNIT ex: "12 Mbps"
    finder = re.compile('([^\w.%=()+-])(\d+)([A-Za-z]+)[^\d]').findall
    for elem in finder(text):
        if elem[-1].lower() != 'html':
            warn(u'Number of unit string need space before unit: "%s"' % u''.join(elem))

    return text2


def validate_ng_words(text, warn=lambda t:None):
    """
    If text include NG words, emit warning.

    :param unicode text: string to validate.
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    if not text:
        return text

    text2 = text

    for ng, good in NG_WORDS:
        if re.findall(ng, text):
            warn(u'NG word found: (%s -> %s)\n%s' % (ng, good, text))

    return text2


VALIDATORS = {
    'term_validator_half_width_katakana': validate_half_width_katakana,
    'term_validator_parenthesis': validate_parenthesis,
    'term_validator_question_exclamation': validate_question_exclamation,
    'term_validator_punctuation_mark': validate_punctuation_mark,
    'term_validator_space_in_number_of_unit': validate_space_in_number_of_unit,
    'term_validator_ng_words': validate_ng_words,
}


def load_ng_word_dic(ng_word_rule_file=None):
    '''
    NGワードの辞書ファイルへのパスを指定します。
    辞書ファイルはUTF-8エンコーディングで、以下の形式で記載します::

        正規表現<tab文字>指摘内容

    :param str ng_word_rule_file:
        * None: use default rule file (default)
        * filepath: path to NG word dic file
    '''
    global NG_WORDS
    if ng_word_rule_file is None:
        rule_file = os.path.join(BASEDIR, 'rule.dic')
    else:
        rule_file = ng_word_rule_file

    with io.open(rule_file, 'rt', encoding='utf-8') as f:
        lines = (line.split('\t', 1) for line in f)
        NG_WORDS = [(ng.strip(), good.strip()) for ng, good in lines]


def doctree_resolved(app, doctree, docname):
    validators = [v for k, v in VALIDATORS.items() if app.config[k]]
    load_ng_word_dic(app.config.term_validator_ng_word_rule_file)


    def text_not_in_literal(node):
        return (isinstance(node, nodes.Text) and
               not isinstance(node.parent,
                              (nodes.literal,
                               nodes.literal_block,
                               nodes.raw,
                               nodes.comment,
                              )) and
               not isinstance(node.parent.parent,
                              (todo_node,
                              ))
               )

    logger_method = getattr(app, app.config.term_validator_loglevel.lower())
    def logger_func(term, lineno):
        location = '%s:%s' % (app.env.doc2path(docname), lineno or '')
        msg = u'%s: term_validator:\n%s' % (location, term)
        logger_method(msg)

    for node in doctree.traverse(text_not_in_literal):
        for validator in validators:
            lineno = node.line or node.parent.line or node.parent.parent.line
            validator(node.astext(), partial(logger_func, lineno=lineno))


def setup(app):

    # :term_validator_half_width_katakana:
    #       半角カタカナが含まれる場合に警告します。
    app.add_config_value('term_validator_half_width_katakana', True, 'env')

    # :term_validator_parenthesis:
    #       半角カッコ()内に全角文字を含む場合に警告します。
    app.add_config_value('term_validator_parenthesis', True, 'env')

    # :term_validator_question_exclamation:
    #       半角疑問符(?)、感嘆符(!)が含まれる場合に警告します。
    app.add_config_value('term_validator_question_exclamation', True, 'env')

    # :term_validator_punctuation_mark:
    #       半角カンマ(,)、ピリオド(.)を含む場合に警告します。
    app.add_config_value('term_validator_punctuation_mark', True, 'env')

    # :term_validator_space_in_number_of_unit:
    #       "12 Mbps" のような数字と単位の間にスペースを含まない場合に警告します。
    app.add_config_value('term_validator_space_in_number_of_unit', True, 'env')

    # :term_validator_ng_words:
    #       `term_validator_ng_word_rule_file` で指定するNGワード辞書に一致する
    #       NGワードが含まれる場合に警告します。
    app.add_config_value('term_validator_ng_words', True, 'env')

    # :term_validator_ng_word_rule_file:
    #       NGワードの辞書ファイルへのパスを指定します。
    #       辞書ファイルは以下の形式で記載します::
    #
    #           正規表現<tab文字>指摘内容
    #
    #       :None: use default rule file (default)
    #       :filepath: (str) path to NG word dic file
    app.add_config_value('term_validator_ng_word_rule_file', None, 'env')

    # :term_validator_loglevel:
    #       log level: info, warn, error
    app.add_config_value('term_validator_loglevel', 'warn', 'env')

    app.connect('doctree-resolved', doctree_resolved)
