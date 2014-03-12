# -*- coding: utf8 -*-
"""
docutils term validation extension

:copyright: Copyright 2011 by Takayuki SHIMIZUKAWA.
:license: Apache Software License 2.0
"""

__docformat__ = 'reStructuredText'

import re
import unicodedata

from docutils.utils import column_width
from docutils import nodes

from sphinx import addnodes
from sphinx.ext.todo import todo_node


def validate_half_width_katakana(text, warn=lambda t:None):
    """
    If text include half-width-katakana, emit warning.

    :param text: string to validate.
    :type text: unicode
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

    :param text: string to validate.
    :type text: unicode
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

    :param text: string to validate.
    :type text: unicode
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    text2 = text

    if column_width(text2) != len(text2):
        text2 = text2.replace(u'?', u'？')
        text2 = text2.replace(u'!', u'！')

    if text != text2:
        warn(u'Half "!", "?" are found\n%s' % text)

    return text2


def validate_punctuation_mark(text, warn=lambda t:None):
    """
    If text include ascii punctuation mark (.,) emit warning.

    :param text: string to validate.
    :type text: unicode
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

    :param text: string to validate.
    :type text: unicode
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    if not text:
        return text

    text2 = text

    # need insert space at NUMBER+UNIT ex: "12 Mbps"
    finder = re.compile('([^\w.=()+-])(\d+)([A-Za-z]+)[^\d]').findall
    for elem in finder(text):
        if elem[-1].lower() != 'html':
            warn(u'Number of unit string need space before unit: "%s"' % u''.join(elem))

    return text2


def validate_ng_words(text, warn=lambda t:None):
    """
    If text include NG words, emit warning.

    :param text: string to validate.
    :type text: unicode
    :param warn: warning function to emit
    :type warn: function accept 1 argument
    :return: normalized string
    :rtype: unicode
    """
    if not text:
        return text

    text2 = text

    ng_words = (
        (ur'だ。|である。', u'ですます調へ'),
        (ur'読み終わる', u'読み終える'),
        (ur'有りま', u'ありま'),
        (ur'例え', u'たとえ'),
        (ur'幾つ', u'いくつ'),
        (ur'沢山', u'たくさん'),
        (ur'様々', u'さまざま'),
        (ur'[^行]為', u'ため'),
        (ur'弊社', u'私たち'),
        (ur'我々', u'私たち'),
        (ur'私達', u'私たち'),
        (ur'ご紹介', u'紹介'),
        (ur'毎', u'ごと'),
        (ur'下さい', u'ください'),
        (ur'わか([ら-ろ])', u'分か（ら|り|る|れ|ろ）'),
        (ur'有る', u'ある'),
        (ur'無(く|い|し)', u'なく, ない, なし'),
        (ur'をを', u'を'),
        (ur'[^執]筆者', u'私たち'),
        (ur'(する(こと|事)が(でき|出来|出き)|出来)[またる]', u'できます'),
        (ur'あなたの', u'読者を引き合いに出さない'),
        (ur'localhost', u'意味のあるサンプルにする'),
        (ur'[\s\n]なので', u'このため'),
        #(ur'やりやすく', u''),
        (ur'ディレクトリー', u'ディレクトリ'),
        (ur'ユーザー', u'ユーザ'),
        (ur'サーバー', u'サーバ'),
        (ur'プログラマー', u'プログラマ'),
        (ur'コンピューター', u'コンピュータ'),
        (ur'ビルダー', u'ビルダ'),
        (ur'ヘッダー', u'ヘッダ'),
        (ur'電子書籍リーダー', u'電子書籍リーダ'),
        #(ur'フォルダ', u'ディレクトリ'),
        #(ur'上がって', u''),
        (ur'挙動になります', u''),
        (ur'叩', u'壊れるから叩いちゃだめ'),
        (ur'[①-⑳]', u'丸数字はNG'),
        (ur'ePub', u'EPUB'),
        (ur'Tex[^ti]', u'TeX'),
        (ur'TeXLive', u'TeX Live'),
        (ur'Mac[^a-zA-Z\s]', u'OS X'),
        (ur'MacOS', u'OS X'),
        (ur'Mac OS X', u'OS X'),
        (ur'[ぁ-んァ-ヶー一-龠] [a-zA-Z0-9]', u'半角文字の前に空白を開けない'),
        (ur'[a-zA-Z] [ぁ-んァ-ヶー一-龠]', u'半角文字の後ろに空白を開けない'),
    )
    for ng, good in ng_words:
        if re.findall(ng, text):
            warn(u'NG word found: (%s -> %s)\n%s' % (ng, good, text))

    return text2


validators = [
    validate_half_width_katakana,
    validate_parenthesis,
    validate_question_exclamation,
    validate_punctuation_mark,
    validate_space_in_number_of_unit,
    validate_ng_words,
]


def doctree_resolved(app, doctree, docname):
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
    for node in doctree.traverse(text_not_in_literal):
        for validator in validators:
            line = node.line or node.parent.line or node.parent.parent.line
            warn = lambda t: app.env.warn(docname, u'term_validator:\n' + t, line)
            validator(node.astext(), warn)


def setup(app):
    app.connect('doctree-resolved', doctree_resolved)
