# -*- coding: utf8 -*-
"""
docutils term validation extension

:copyright: Copyright 2011 by Takayuki SHIMIZUKAWA.
:license: Apache Software License 2.0
"""
import io
import os
import re
import unicodedata
from functools import partial
from sphinx.util import logging
import difflib
import textwrap

from docutils.utils import column_width
from docutils import nodes

from sphinx.ext.todo import todo_node

__docformat__ = 'reStructuredText'

BASEDIR = os.path.dirname(os.path.abspath(__file__))

NG_WORDS = []

logger = logging.getLogger(__name__)
default_warn_logger = logger.warning

# compiled re objects
find_parethesis = re.compile(r'\(([^)]*)\)').findall
find_question_exclamation = re.compile(r'([ぁ-んァ-ヶー一-龠]+)([!?]+)').findall
sub_dot_space = re.compile(r'([^\d,.])\. ').sub
sub_dot_newline = re.compile(r'([^\d,.])\.\n').sub
sub_dot_eol = re.compile(r'([^\d,.])\.$').sub
sub_comma_space = re.compile(r'([^,.]), ').sub
sub_comma_newline = re.compile(r'([^,.]),\n').sub
sub_comma_eol = re.compile(r'([^,.]),$').sub
find_numofunit = re.compile(r'([^\w.%=()+-])(\d+)([A-Za-z]+)[^\d]').findall


indent = partial(textwrap.indent, prefix='  ')


def differ(text1, text2):
    texts = [
        (t.strip() + '\n').splitlines(keepends=True)
        for t in (text1, text2)
    ]
    diff = difflib.Differ().compare(texts[0], texts[1])
    return ''.join(diff)


class ValidationErrorMessage(object):
    def __init__(self, error_type,node, target_text, suggestion_text,
                 source=None, lineno=None):
        self.error_type = error_type
        self.node = node
        self.target_text = target_text
        self.suggestion_text = suggestion_text
        self.source = source
        self.lineno = lineno

    def __str__(self):
        if len(self.target_text) < 10 and len(self.suggestion_text) < 10:
            return u'{etype}: ({target} -> {suggestion})\n{node}'.format(
                etype=self.error_type,
                target=self.target_text,
                suggestion=self.suggestion_text,
                node=indent(self.node.astext()),
            )
        else:
            return u'{etype}:\n{diff}'.format(
                etype=self.error_type,
                diff=differ(self.target_text, self.suggestion_text),
            )


def system_message(vmsg, source, lineno):
    """
    :param ValidationErrorMessage vmsg: message object
    :param source: file path
    :param lineno: lineno
    :return: system_message node
    """
    msg = u'{etype}: {target} -> {suggestion}'.format(
        etype=vmsg.error_type,
        target=vmsg.target_text,
        suggestion=vmsg.suggestion_text,
    )
    return nodes.system_message(
        msg, type='WARNING', level=2, source=source, lineno=lineno
    )


def validate_half_width_katakana(node):
    """
    If text include half-width-katakana, emit warning.

    :param docutils.nodes.Node node: node to validate.
    :return: list of validation error messages
    :rtype: List[ValidationErrorMessage]
    """
    chars = []
    for t in node.astext():
        if unicodedata.category(t)[0] in ('L', 'N'):
            chars.append(unicodedata.normalize('NFKC', t))
        else:
            chars.append(t)

    text = ''.join(chars)
    msgs = []
    if node.astext() != text:
        msg = ValidationErrorMessage(
            'Wide ascii, Wide number or Half kana',
            node, node.astext(), text)
        msgs.append(msg)

    return msgs


def validate_parenthesis(node):
    """
    If text include half parenthesis within wide text, emit warning.

    :param docutils.nodes.Node node: node to validate.
    :return: list of validation error messages
    :rtype: List[ValidationErrorMessage]
    """
    text = node.astext()

    msgs = []
    for term in find_parethesis(text):
        if column_width(term) != len(term):
            old_text = text
            text = text.replace(u'(%s)' % term, u'（%s）' % term)
            msg = ValidationErrorMessage(
                'Half parenthesis include Wide string',
                node, old_text, text)
            msgs.append(msg)

    return msgs


def validate_question_exclamation(node):
    """
    If text include half question or exclamatoin, emit warning.

    :param docutils.nodes.Node node: node to validate.
    :return: list of validation error messages
    :rtype: List[ValidationErrorMessage]
    """
    text = node.astext()

    if column_width(text) != len(text):
        for base, mark in find_question_exclamation(text):
            wide_mark = mark.replace(u'!', u'！').replace(u'?', u'？')
            text = text.replace(base + mark, base + wide_mark)

    msgs = []
    if text != node.astext():
        msg = ValidationErrorMessage(
            'Half "!", "?" after full-width char',
            node, node.astext(), text)
        msgs.append(msg)

    return msgs


def validate_punctuation_mark(node):
    """
    If text include ascii punctuation mark (.,) emit warning.

    :param docutils.nodes.Node node: node to validate.
    :return: list of validation error messages
    :rtype: List[ValidationErrorMessage]
    """
    text = node.astext()
    if not text:
        return []

    if column_width(text) == len(text):
        return []

    # replace . with 。
    text = sub_dot_space(u'\\1。',   text)  # ドット+スペース
    text = sub_dot_newline(u'\\1。\n', text)  # ドット+改行
    text = sub_dot_eol(u'\\1。',   text)  # ドット+終端
    # replace , with 、
    text = sub_comma_space(u'\\1、',   text)  # カンマ+スペース
    text = sub_comma_newline(u'\\1、\n', text)  # カンマ+改行
    text = sub_comma_eol(u'\\1、',   text)  # カンマ+終端

    msgs = []
    if text != node.astext():
        msg = ValidationErrorMessage(
            'ASCII punctuation mark', node, node.astext(), text)
        msgs.append(msg)

    return msgs


def validate_space_in_number_of_unit(node):
    """
    If text did not include space in number of unit as "12 Mbps", emit warning.

    :param docutils.nodes.Node node: node to validate.
    :return: list of validation error messages
    :rtype: List[ValidationErrorMessage]
    """
    text = node.astext()
    if not text:
        return []

    # need insert space at NUMBER+UNIT ex: "12 Mbps"
    msgs = []
    for elem in find_numofunit(text):
        if elem[-1].lower() != 'html':
            msg = ValidationErrorMessage(
                'Space in number of unit', node, u''.join(elem),
                'Number of unit string need space before unit')
            msgs.append(msg)

    return msgs


def validate_ng_words(node):
    """
    If text include NG words, emit warning.

    :param docutils.nodes.Node node: node to validate.
    :return: list of validation error messages
    :rtype: List[ValidationErrorMessage]
    """
    text = node.astext()
    if not text:
        return []

    msgs = []
    for finder, ng, good in NG_WORDS:
        found = finder(text)
        if found:
            msg = ValidationErrorMessage(
                'NG word', node, found.group(0), good)
            msgs.append(msg)

    return msgs


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

    空行と、行頭が#の行はスキップします

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
        lines = (
            line.split('\t', 1)
            for line in f
            if (line) and (not line.startswith('#')) and ('\t' in line)
        )
        NG_WORDS = [
            (re.compile('(%s)' % ng.strip()).search, ng.strip(), good.strip())
            for ng, good in lines
        ]


def doctree_resolved(app, doctree, docname):
    validators = [v for k, v in VALIDATORS.items() if app.config[k]]
    load_ng_word_dic(app.config.term_validator_ng_word_rule_file)

    def isdescendant(node, types):
        while node is not None:
            if isinstance(node, types):
                return True
            node = node.parent
        return False

    def text_not_in_literal(node):
        return (isinstance(node, nodes.Text) and
               not isdescendant(node.parent,
                                (nodes.literal,
                                 nodes.literal_block,
                                 nodes.raw,
                                 nodes.comment,
                                 todo_node,
                                ))
               )

    logger_method = getattr(logger, app.config.term_validator_loglevel.lower())

    source = app.env.doc2path(docname)

    for node in doctree.traverse(text_not_in_literal):
        for validator in validators:
            lineno = node.line or node.parent.line or node.parent.parent.line
            msgs = validator(node)
            if 1:  # もしconsoleならmsgsをlogger_funcに流す
                for msg in msgs:
                    logger_method(u'%s:%s sphinx_term_validator:\n%s' %
                                  (source, lineno, indent(msg)))
            if 1:  # ページ埋め込みなら、nodeに追加する
                for msg in msgs:
                    sm = system_message(msg, source, lineno)
                    node.parent += sm


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
    app.add_config_value('term_validator_loglevel', 'warning', 'env')

    app.connect('doctree-resolved', doctree_resolved)
