========================
sphinx-term-validator
========================

sphinx-term-validator はドキュメントの単語を検査するSphinx拡張です。

rule.dic ファイルに記載された正規表現に一致する記述をドキュメントからみつけて、警告を表示します。
警告はドキュメントのビルド時に表示されます。

実行例
========

ドキュメントビルド時にルール辞書に従って文字列を検査します。
正規表現で書かれたルールに一致した文字列があると、警告を出力します。
例::

   $ make html
   ...
   WARNING: /source/index.rst:100: term_validator:
   NG word found: (出来[^事] -> でき)
   ...

ルール辞書
============

ルール辞書ファイルは以下の形式で記載します::
   
   正規表現<tab文字>指摘内容

例::

   ディレクトリー	ディレクトリ
   ユーザ[^ー]	ユーザー
   サーバ[^ー]	サーバー
   [\s\n]なので	このため
   出来[^事]	でき
   (する(こと|事)が(でき|出来|出き)|出来)[またる]	できます

詳しくは、rule.dic を参照してください。

conf.py
===========

以下の設定を行えます。

:term_validator_half_width_katakana:
   半角カタカナが含まれる場合に警告します。デフォルトはTrueです。

:term_validator_parenthesis:
   半角カッコ()内に全角文字を含む場合に警告します。デフォルトはTrueです。

:term_validator_question_exclamation:
   半角疑問符(?)、感嘆符(!)が含まれる場合に警告します。デフォルトはTrueです。

:term_validator_punctuation_mark:
   半角カンマ(,)、ピリオド(.)を含む場合に警告します。デフォルトはTrueです。

:term_validator_space_in_number_of_unit:
   "12 Mbps" のような数字と単位の間にスペースを含まない場合に警告します。デフォルトはTrueです。

:term_validator_ng_words:
   NGワード辞書に一致する文字列が含まれる場合に警告します。デフォルトはTrueです。

:term_validator_ng_word_rule_file:
   NGワードの辞書ファイルへのパスを指定します。
   デフォルトで、このsphinx-term-validator拡張のあるディレクトリのrule.dicを使用します。
      
:term_validator_loglevel:
   警告ログのレベルを指定します。レベルは ``info``, ``warn``, ``error`` から指定します。
   デフォルトは ``warn`` です。

LICENSE
==========

Apache Software License 2.0