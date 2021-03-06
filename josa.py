# josa

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import config
from flags import *
from jamo import *
import suffix

import unicodedata

def NFD(unistr):
    return unicodedata.normalize('NFD', unistr)
def NFC(unistr):
    return unicodedata.normalize('NFC', unistr)

ALPHA_ALL = ''.join([chr(c) for c in range(ord('0'),ord('9')+1)] + [chr(c) for c in range(ord('a'),ord('z')+1)])

## 임의로 허용하는 로마자로 된 단어는 음운 구별을 하지 않는다. 할 방법이 없음.
COND_ALL = '.'
COND_V_ALL = '[%s]' % (V_ALL + ALPHA_ALL)
COND_T_ALL = '[%s]' % (T_ALL + ALPHA_ALL)
COND_V_OR_RIEUL = '[%s]' % (V_ALL + T_RIEUL + ALPHA_ALL)
COND_T_NOT_RIEUL = '[%s]' % (T_ALL.replace(T_RIEUL, '') + ALPHA_ALL)

class JosaClass:
    next_flag = josas_flag_start
    def __init__(self, rules=[], after=[], notafter=[]):
        self.rules = rules
        self.after = after
        self.notafter = notafter
        self.flag = JosaClass.next_flag
        JosaClass.next_flag += 1
    def match(self, word, pos, props):
        if self.notafter:
            if (word, '#' + pos) in self.notafter:
                return False
        if self.after:
            # 부사는 상태부사, 성상부사, 정도부사, 양태부사만 보조사 허용
            if pos.startswith('부사'):
                if pos in ['부사:상태', '부사:성상', '부사:정도', '부사:양태']:
                    pos = '부사'
                else:
                    return False

            if ('#' + pos) in self.after:
                return True
            elif (word, '#' + pos) in self.after:
                return True
            else:
                return False
        return True
    def output(self):
        result = []
        line = 'SFX %d Y %d' % (self.flag, len(self.rules))
        result.append(NFD(line))
        for (sfx, cond, strip) in self.rules:
            if not strip:
                strip = '0'
            if not cond:
                cond = '.'
            line = 'SFX %d %s %s %s' % (self.flag, strip, sfx, cond)
            result.append(NFD(line))
        return '\n'.join(result)


##
##

groups = {}

## '이' 주격/보격 조사
groups['이'] = [
    JosaClass(
        rules = [('이', COND_T_ALL, '')],
        after = ['#명사', '#대명사'],
    ),
    # 대명사 '-거'+'이' -> '게'
    JosaClass(
        rules = [(V_E, '거', V_EO)],
        after = [('거', '#대명사'),
                 ('그거', '#대명사'),
                 ('요거', '#대명사'),
                 ('이거', '#대명사'),
                 ('저거', '#대명사'),
                ],
    ),
]

# '가' 주격/보격 조사
groups['가'] = [
    JosaClass(
        rules = [('가', COND_V_ALL, '')],
        after = ['#명사', '#대명사',
                 '#특수:숫자', '#특수:알파벳',
                 '#특수:수:1', '#특수:수:10', '#특수:수:100', '#특수:수:1000',
                 '#특수:고유수:1', '#특수:고유수:10',
                 ],
        notafter = [('나', '#대명사'),
                    ('너', '#대명사'),
                    ('저', '#대명사'),
                   ],
    ),
    # 대명사 '나'+'가' -> '내가', '너'+'가' -> '네가', '저'+'가' -> '제가'
    JosaClass(
        rules = [(V_AE + '가', V_A, V_A),
                 (V_E + '가', V_EO, V_EO),
                 ],
        after = [('나', '#대명사'),
                 ('너', '#대명사'),
                 ('저', '#대명사'),
                ],
    ),
    # 대명사 '누구'+'가' -> '누가'
    JosaClass(
        rules = [('가', '누구', '구')],
        after = [('누구', '#대명사')],
    ),
]

groups['!대명사+의'] = [
    # 대명사 '나'+'의' -> '내', '너'+'의' -> '네', '저'+'의' -> '제'
    JosaClass(
        rules = [(V_AE, V_A, V_A),
                 (V_E, V_EO, V_EO),
                 (V_E, V_EO, V_EO),
                ],
        after = [('나', '#대명사'),
                 ('너', '#대명사'),
                 ('저', '#대명사'),
                ],
    ),
]

# '-ㄴ', '-ㄹ' 형태로 줄여진 구어체
groups['!종성줄임'] = [
    JosaClass(
        rules = [(T_RIEUL, COND_V_ALL, ''),
                 (T_NIEUN, COND_V_ALL, '')],
        after = ['#명사', '#대명사'],
    ),
]

# '거'+'로' => '걸로'
groups['!거+로'] = [
    JosaClass(
        rules = [(T_RIEUL + '로' + emph, '거', '')
                 for emph in ['', '는', T_RIEUL, '도',
                              '만',
                              '서', '서는', '선', '서도',
                              '써', '써는', '썬', '써도',
                              '부터', '부터는', '부턴', '부터도']],
        after = [('거', '#대명사'),
                 ('그거', '#대명사'),
                 ('요거', '#대명사'),
                 ('이거', '#대명사'),
                 ('저거', '#대명사'),
                ],
    ),
]

# 보조사
groups['!보조사'] = [
    JosaClass(
        rules = [('도', COND_ALL, ''),
                 ('만', COND_ALL, ''),
                 ('은', COND_T_ALL, ''), ('는', COND_V_ALL, ''),
                 ('은커녕', COND_T_ALL, ''), ('는커녕', COND_V_ALL, ''),
                ],
        after = ['#부사',
                 '#명사', '#대명사', '#수사',
                 '#특수:숫자', '#특수:알파벳',
                 '#특수:수:1', '#특수:수:10', '#특수:수:100', '#특수:수:1000',
                 '#특수:고유수:1', '#특수:고유수:10',
                 ],
    ),
]

groups['*'] = [
    JosaClass(
        rules = [
         ('을', COND_T_ALL, ''), ('를', COND_V_ALL, ''),
         ('과', COND_T_ALL, ''), ('와', COND_V_ALL, ''),
         ('과는', COND_T_ALL, ''), ('와는', COND_V_ALL, ''),
         ('관', COND_T_ALL, ''), ('완', COND_V_ALL, ''),
         ('과도', COND_T_ALL, ''), ('와도', COND_V_ALL, ''),
         ('과의', COND_T_ALL, ''), ('와의', COND_V_ALL, ''),
         ('라', COND_V_ALL, ''), ('이라', COND_T_ALL, ''),
         ('라고', COND_V_ALL, ''), ('이라고', COND_T_ALL, ''),
         ('라는', COND_V_ALL, ''), ('이라는', COND_T_ALL, ''),
         ('라도', COND_V_ALL, ''), ('이라도', COND_T_ALL, ''),
         ('라면', COND_V_ALL, ''), ('이라면', COND_T_ALL, ''),
         ('라서', COND_V_ALL, ''), ('이라서', COND_T_ALL, ''),
         ('란', COND_V_ALL, ''), ('이란', COND_T_ALL, ''),
         ('랑', COND_V_ALL, ''), ('이랑', COND_T_ALL, ''),
         ('로', COND_V_OR_RIEUL, ''), ('으로', COND_T_NOT_RIEUL, ''),
         ('로는', COND_V_OR_RIEUL, ''), ('으로는', COND_T_NOT_RIEUL, ''),
         ('론', COND_V_OR_RIEUL, ''), ('으론', COND_T_NOT_RIEUL, ''),
         ('로의', COND_V_OR_RIEUL, ''), ('으로의', COND_T_NOT_RIEUL, ''),
         ('로도', COND_V_OR_RIEUL, ''), ('으로도', COND_T_NOT_RIEUL, ''),
         ('로만', COND_V_OR_RIEUL, ''), ('으로만', COND_T_NOT_RIEUL, ''),
         ('로밖에', COND_V_OR_RIEUL, ''), ('으로밖에', COND_T_NOT_RIEUL, ''),
         ('로부터', COND_V_OR_RIEUL, ''), ('으로부터', COND_T_NOT_RIEUL, ''),
         ('로부터는', COND_V_OR_RIEUL, ''), ('으로부터는', COND_T_NOT_RIEUL, ''),
         ('로부턴', COND_V_OR_RIEUL, ''), ('으로부턴', COND_T_NOT_RIEUL, ''),
         ('로부터도', COND_V_OR_RIEUL, ''), ('으로부터도', COND_T_NOT_RIEUL, ''),
         ('로부터의', COND_V_OR_RIEUL, ''), ('으로부터의', COND_T_NOT_RIEUL, ''),
         ('로서', COND_V_OR_RIEUL, ''), ('으로서', COND_T_NOT_RIEUL, ''),
         ('로서는', COND_V_OR_RIEUL, ''), ('으로서는', COND_T_NOT_RIEUL, ''),
         ('로선', COND_V_OR_RIEUL, ''), ('으로선', COND_T_NOT_RIEUL, ''),
         ('로서도', COND_V_OR_RIEUL, ''), ('으로서도', COND_T_NOT_RIEUL, ''),
         ('로서의', COND_V_OR_RIEUL, ''), ('으로서의', COND_T_NOT_RIEUL, ''),
         ('로써', COND_V_OR_RIEUL, ''), ('으로써', COND_T_NOT_RIEUL, ''),
         ('로써는', COND_V_OR_RIEUL, ''), ('으로써는', COND_T_NOT_RIEUL, ''),
         ('로썬', COND_V_OR_RIEUL, ''), ('으로썬', COND_T_NOT_RIEUL, ''),
         ('로써도', COND_V_OR_RIEUL, ''), ('으로써도', COND_T_NOT_RIEUL, ''),
         ('야말로', COND_V_ALL, ''), ('이야말로', COND_T_ALL, ''),

         # sorted list
         ('같이', COND_ALL, ''),
         ('까지', COND_ALL, ''),
         ('까지는', COND_ALL, ''),
         ('까진', COND_ALL, ''),
         ('까지도', COND_ALL, ''),
         ('까지만', COND_ALL, ''),
         ('까지라도', COND_ALL, ''),
         ('께', COND_ALL, ''),
         ('께는', COND_ALL, ''),
         ('껜', COND_ALL, ''),
         ('께도', COND_ALL, ''),
         ('께서', COND_ALL, ''),
         ('께서는', COND_ALL, ''),
         ('께선', COND_ALL, ''),
         ('께서도', COND_ALL, ''),
         ('끼리', COND_ALL, ''), # TODO: -끼리: 가산명사에만 붙음
         ('나', COND_V_ALL, ''),
         ('대로', COND_ALL, ''),
         ('대로는', COND_ALL, ''),
         ('대론', COND_ALL, ''),
         ('대로만', COND_ALL, ''),
         ('대로의', COND_ALL, ''),
         # TODO: -더러 조사는 사람이나 동물 등에만 붙음
         ('더러', COND_ALL, ''),
         ('더러는', COND_ALL, ''),
         ('더러만', COND_ALL, ''),
         ('더런', COND_ALL, ''),
         ('마다', COND_ALL, ''),         # 보조사, '모두'
         ('마저', COND_ALL, ''),
         ('마저도', COND_ALL, ''),
         ('만의', COND_ALL, ''),
         ('만이', COND_ALL, ''),
         ('만큼', COND_ALL, ''),
         ('밖에', COND_ALL, ''),
         ('밖에는', COND_ALL, ''),
         ('밖엔', COND_ALL, ''),
         ('보다', COND_ALL, ''),
         ('보다는', COND_ALL, ''),
         ('보단', COND_ALL, ''),
         ('보다도', COND_ALL, ''),
         ('부터', COND_ALL, ''),
         ('부터는', COND_ALL, ''),
         ('부턴', COND_ALL, ''),
         ('부터라도', COND_ALL, ''),
         ('서', COND_ALL, ''),           # '~에서' 준말
         ('에', COND_ALL, ''),
         ('에게', COND_ALL, ''),
         ('에게는', COND_ALL, ''),
         ('에겐', COND_ALL, ''),
         ('에게도', COND_ALL, ''),
         ('에게만', COND_ALL, ''),
         ('에게서', COND_ALL, ''),
         ('에게서는', COND_ALL, ''),
         ('에게서도', COND_ALL, ''),
         ('에게서만', COND_ALL, ''),
         ('에는', COND_ALL, ''),         # 에+'는' 보조사
         ('에라도', COND_ALL, ''),       # 에+'라도' 보조사
         ('에야', COND_ALL, ''),         # 에+'야' 보조사
         ('엔', COND_ALL, ''),           # '에는' 준말
         ('에나', COND_ALL, ''),         # 에+'나' 보조사
         ('에도', COND_ALL, ''),         # 에+'도' 보조사
         ('에만', COND_ALL, ''),         # 에+'만' 보조사
         ('에서', COND_ALL, ''),
         ('에서는', COND_ALL, ''),       # 에서+'는' 보조사
         ('에선', COND_ALL, ''),
         ('에서도', COND_ALL, ''),       # 에서+'도' 보조사
         ('에서만', COND_ALL, ''),       # 에서+'만' 보조사
         ('야', COND_V_ALL, ''),
         ('의', COND_ALL, ''),
         ('이나', COND_T_ALL, ''),
         ('이든', COND_ALL, ''),
         ('이든지', COND_ALL, ''),
         ('이야', COND_T_ALL, ''), # '-(이, '')야' 강조
         ('조차', COND_ALL, ''),
         ('조차도', COND_ALL, ''),
         ('처럼', COND_ALL, ''),
         ('처럼은', COND_ALL, ''),
         ('커녕', COND_ALL, ''),
         # TODO: -한테 조사는 사람이나 동물 등에만 붙음
         ('하고', COND_ALL, ''),         # 구어체
         ('한테', COND_ALL, ''),
         ('한테는', COND_ALL, ''),
         ('한텐', COND_ALL, ''),
         ('한테도', COND_ALL, ''),
         ('한테서', COND_ALL, ''),
         ],
        after = ['#명사', '#대명사', '#수사',
                 '#특수:숫자', '#특수:알파벳',
                 '#특수:수:1', '#특수:수:10', '#특수:수:100', '#특수:수:1000',
                 '#특수:고유수:1', '#특수:고유수:10',
                 ],
    ),
]

klasses = []

# FIXME: 임시
for _key in groups.keys():
    klasses += groups[_key]

def find_flags(word, pos, props):
    result = []
    for klass in klasses:
        if klass.match(word, pos, props):
            result.append(klass.flag)
    if (pos == '명사' or pos == '대명사' or pos == '특수:복수접미사' or
        pos == '특수:알파벳' or pos == '특수:숫자' or
        pos.startswith('특수:수:')):
        result.append(josa_ida_flag)
    if (pos == '대명사'):
        result.append(josa_ida_t_flag)
    return result

def get_ida_rules(flagaliases):
    ida_josas = []
    ida_josas_t = []
    # 주격조사 ('이다') 활용을 조사 목록에 덧붙이기
    # twofold suffix를 여기에 써먹기에는 아깝다
    ida_conjugations = suffix.make_all_conjugations('이다', '이다', [])
    for c in ida_conjugations:
        if flagaliases and '/' in c:
            (word,flags_str) = c.split('/')
            cont_flags = [int(s) for s in flags_str.split(',')]
            if not cont_flags in flagaliases:
                flagaliases.append(cont_flags)
            c = word + '/%d' % (flagaliases.index(cont_flags) + 1)
        if (NFD(c)[:2] == NFD('여') or
            NFD(c)[:2] == NFD('예')):
            # '이어' -> '여', '이에' => '예' 줄임형은 받침이 있을 경우에만
            ida_josas.append((c, COND_V_ALL))
        else:
            ida_josas.append((c, COND_ALL))
        # '이' 생략
        # TODO: 받침이 앞의 명사에 붙는 경우 허용 여부 (예: "마찬가집니다")
        if NFC(c)[0] == '이':
            ida_josas.append((NFC(c)[1:], COND_V_ALL))
        elif NFD(c)[:2] == NFD('이'):
            ida_josas_t.append((NFD(c)[2:], COND_V_ALL))

    result = ['SFX %d Y %d' % (josa_ida_flag, len(ida_josas))]
    for (sfx,cond) in ida_josas:
        result.append(NFD('SFX %d 0 %s %s' % (josa_ida_flag, sfx, cond)))

    result.append('SFX %d Y %d' % (josa_ida_t_flag, len(ida_josas_t)))
    for (sfx,cond) in ida_josas_t:
        result.append(NFD('SFX %d 0 %s %s' % (josa_ida_t_flag, sfx, cond)))
    return result
    
def get_output(flagaliases):
    result = []
    for klass in klasses:
        result.append(klass.output())
    result += get_ida_rules(flagaliases)
    return '\n'.join(result)
