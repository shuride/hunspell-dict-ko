# -*- coding: utf-8 -*-
# 용언/서술격조사 활용

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Hunspell Korean spellchecking dictionary.
#
# The Initial Developer of the Original Code is
# Changwoo Ryu.
# Portions created by the Initial Developer are Copyright (C) 2008
# the Initial Developer. All Rights Reserved.
#
# Contributor(s): Changwoo Ryu <cwryu@debian.org>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import sys
reload(sys)
sys.setdefaultencoding('UTF-8')
import re
import unicodedata

import config
from suffixdata import groups

def NFD(unistr):
    return unicodedata.normalize('NFD', unistr)
def NFC(unistr):
    return unicodedata.normalize('NFC', unistr)

# 조건이 list일 경우 확장
def expand_by_cond():
    for key in groups.keys():
        for klass in groups[key]:
            new_rules = []
            for rule in klass['rules']:
                if type(rule[1]) == type([]):
                    for c in rule[1]:
                        new_rules.append([rule[0], c] + rule[2:])
                else:
                    new_rules.append(rule)
            klass['rules'] = new_rules
    #return groups

# 조건 정리
def clean_up_cond():
    for key in groups.keys():
        for klass in groups[key]:
            for c in ['after', 'notafter', 'cond', 'notcond']:
                if not klass.has_key(c):
                    continue
                new = set()
                for item in klass[c]:
                    if item == '#용언':
                        new.add('#동사')
                        new.add('#형용사')
                    else:
                        new.add(item)
                klass[c] = sorted(list(new))
    return groups

# 선어말어미 연결
def expand_by_link():
    # 임시로 마지막 어미의 키워드 부착: 집에서 따라하지 마세요 :P
    for key in groups.keys():
        for klass in groups[key]:
            for rule in klass['rules']:
                rule.append(key)

    refgroups = groups.copy()

    def find_rules_to_attach(last):
        rules = []
        for key in refgroups.keys():
            g = refgroups[key]
            for k in g:
                if (('-' in k['after'] or last in k['after']) and
                    (not k.has_key('notafter') or not last in k['notafter'])):
                    for r in k['rules']:
                        if re.match(NFD(u'.*' + r[1] + '$'), NFD(last[:-1])):
                            rules.append(r)
        return rules

    def expand_class(klass):
        while True:
            rules_to_expand = [r for r in klass['rules'] if r[0][-1] == '-']
            if not rules_to_expand:
                return

            new_rules = [r for r in klass['rules'] if r[0][-1] != '-']
            for r in rules_to_expand:
                last = r[-1]
                attaches = find_rules_to_attach(last)
                for a in attaches:
                    if a[2]:
                        striplen = len(NFD(a[2]))
                    else:
                        striplen = 0
                    new_suffix = NFC(NFD(r[0])[:-1-striplen] + a[0][1:])
                    new_rules.append([new_suffix] + r[1:3] + a[3:])
            klass['rules'] = new_rules

    for key in groups.keys():
        if key[-1] != '-':
            continue
        for klass in groups[key]:
            expand_class(klass)

    # 임시로 부착했던 마지막 어미 키워드 삭제
    for key in groups.keys():
        for klass in groups[key]:
            for rule in klass['rules']:
                del rule[-1]

expand_by_cond()
clean_up_cond()
expand_by_link()

# 연결이 끝나면 그룹끼리 구분할 필요가 없다.
klasses = []
for key in groups.keys():
    klasses += groups[key]
del groups

# 선어말어미 연결 정보도 필요 없다.
for klass in klasses:
    for condname in ['after', 'notafter']:
        try:
            klass[condname] = [c for c in klass[condname] if c[0] != '-']
        except:
            pass

# 같은 조건의 클래스를 머지한다.
def eq_klass_cond(a, b):
    for condname in ['after', 'notafter', 'cond', 'notcond']:
        if a.has_key(condname) and b.has_key(condname):
            if a[condname] != b[condname]:
                return False
        elif a.has_key(condname) or b.has_key(condname):
            return False
    return True
new_klasses = []
for klass in klasses:           # 무식한 방법이지만 간단히...
    for new_klass in new_klasses:
        if eq_klass_cond(klass, new_klass):
            new_klass['rules'] += klass['rules']
            break
    else:
        new_klasses.append(klass)        
klasses = new_klasses
del new_klasses

# flag 부착
def attach_flags():
    count = 0
    for klass in klasses:
        klass['flag'] = (config.endings_flag_start + count)
        count = count + 1
attach_flags()


######################################################################
## 외부 사용

def write_suffixes(file):
    for klass in klasses:
        flag = klass['flag']
        file.write('SFX %d Y %d\n' % (flag, len(klass['rules'])))
        for r in klass['rules']:
            suffix = r[0][1:] # 앞에 '-' 빼기
            condition = r[1] + '다'
            strip = r[2] + '다'
            try:
                cont = ','.join(['%d' % c for c in r[3]])
                sys.stderr.write('suffix: %s, cont: %s' % (suffix, cont))
                file.write(NFD('SFX %d %s %s/%s %s\n' %
                               (flag, strip, suffix, cont, condition)))
            except IndexError:
                file.write(NFD('SFX %d %s %s %s\n' %
                               (flag, strip, suffix, condition)))

def class_match_word(klass, word, po, props):
    if (klass.has_key('after') and
        (not word in klass['after']) and (not ('#'+po) in klass['after'])):
        return False
    if (klass.has_key('notafter') and
        ((word in klass['notafter']) or (not ('#'+po) in klass['after']))):
        return False
    if klass.has_key('cond'):
        for prop in props:
            if ('#'+prop) in klass['cond']:
                break;
        else:
            return False
    if klass.has_key('notcond'):
        for prop in props:
            if ('#'+prop) in klass['notcond']:
                return False;
    return True

# 해당되는 flag 찾기
def find_flags(word, po, props):
    result = []
    for klass in klasses:
        if class_match_word(klass, word, po, props):
            result.append(klass['flag'])
    return result
            
    
# 가능한 모든 활용 형태 만들기
def make_conjugations(word, po, props):
    result = []
    for klass in klasses:
        if not class_match_word(klass, word, po, props):
            continue
        
        for r in klass['rules']:
            if re.match(NFD(u'.*' + r[1] + '다$'), NFD(word)):
                if r[2]:
                    striplen = len(NFD(r[2] + u'다'))
                else:
                    striplen = len(NFD(u'다'))
                result.append(NFC(NFD(word)[:-striplen] + r[0][1:]))
    return result
