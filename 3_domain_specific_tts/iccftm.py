import numpy as np
import subprocess
import random

from tools import read_audio, save_audio

def say_phrase(sl_phrase: list, out_path:str = './data_LO/ex.wav', play: bool = False, print: bool = True, question: bool = False):
    '''
    Takes in list e.g. ["the", "first", "month_is", "January"] and saves a synthesized
    waveform for the phrase at <out_path>
    '''
    parts = []
    text = ''
    first = True
    for seg in sl_phrase:
        if first is True:
            _, sr = read_audio(f'./data_LO/{seg}.wav')
            first = False
        parts.append(generate_seg(seg))
        text += seg.replace('_', ' ') + ' '
    text = text.rstrip()
    if question is True:
        text += '?'

    output = splice(parts)

    save_audio(output, sr, out_path)

    if play:
        subprocess.call(['play', out_path])

def generate_seg(seg):
    part, _ = read_audio(f'./data_LO/{seg}.wav')
    return part

def splice(parts):
    return np.hstack(parts)

def generate_buttons(question_num, word_bank):
    words = q_data[question_num]["isl_toks"].copy()
    words += random.sample(word_bank, 4)
    random.shuffle(words)
    return words

def grade_phrase(isl_phrase: list, question_num: int):
    print('submitted:', isl_phrase)
    print('correct:', q_data[question_num]['isl_toks'])
    if isl_phrase == q_data[question_num]['isl_toks']:
        return give_pos_feedback(question_num)
    else:
        return give_neg_feedback(question_num)
    # say_phrase(["viltu_spila_aftur"], play=True) 

def give_pos_feedback(question_num):
    print('yes')
    return ([random.choice(pos_feedback)], q_data[question_num]['isl_toks'])

def give_neg_feedback(question_num):
    print('no')
    return ([random.choice(neg_feedback)], [random.choice(should_be_phrases)] + q_data[question_num]['isl_toks'])


q_data = {
1: {"eng_toks": ["the", "first", "month_is", "January"], "isl_toks": ["fyrsti", "mánuðurinn", "er", "janúar"]},
2: {"eng_toks": ["the", "second", "month_is", "February"], "isl_toks": ["annar", "mánuðurinn", "er", "febrúar"]},
3: {"eng_toks": ["the", "third", "month_is", "March"], "isl_toks": ["þriðji", "mánuðurinn", "er", "mars"]},
4: {"eng_toks": ["the", "fourth", "month_is", "April"], "isl_toks": ["fjórði", "mánuðurinn", "er", "apríl"]},
5: {"eng_toks": ["the", "fifth", "month_is", "May"], "isl_toks": ["fimmti", "mánuðurinn", "er", "maí"]},
6: {"eng_toks": ["the", "sixth", "month_is", "June"], "isl_toks": ["sjötti", "mánuðurinn", "er", "júní"]},
7: {"eng_toks": ["the", "seventh", "month_is", "July"], "isl_toks": ["sjöundi", "mánuðurinn", "er", "júlí"]},
8: {"eng_toks": ["the", "eighth", "month_is", "August"], "isl_toks": ["áttundi", "mánuðurinn", "er", "ágúst"]},
9: {"eng_toks": ["the", "ninth", "month_is", "September"], "isl_toks": ["níundi", "mánuðurinn", "er", "september"]},
10: {"eng_toks": ["the", "tenth", "month_is", "October"], "isl_toks": ["tíundi", "mánuðurinn", "er", "október"]},
11: {"eng_toks": ["the", "eleventh", "month_is", "November"], "isl_toks": ["ellefti", "mánuðurinn", "er", "nóvember"]},
12: {"eng_toks": ["the", "twelfth", "month_is", "December"], "isl_toks": ["tólfti", "mánuðurinn", "er", "desember"]}
}

word_bank = ["annar", "apríl", "desember", "ellefti", "er", "febrúar", "fimmti", "fjórði", "fyrsti", "janúar", "júlí", "júní", "mars", "maí", "mánuður", "mánuðurinn", "níundi", "nóvember", "október", "september", "sjötti", "sjöundi", "tíundi", "tólfti", "ágúst", "áttundi", "þriðji", "fyrsta", "annað", "níu", "tveir", "sól", "daginn"]
pos_feedback = ["já_það_er_rétt", "vá_íslenskan_þín_er_frábær", "vel_gert", "þú_ert_ótrúlega_klár"]
neg_feedback = ["nei,_það_er_rangt", "ertu_heimskur_eða_hvað", "ertu_að_grínast_núna"]
should_be_phrases = ["á_íslensku_er_það", "á_íslensku_segir_maður", "setningin_ætti_að_vera"]

if __name__ == '__main__':
    say_phrase(["hæ_og_velkomin_í_tungumálaforritið_sem_heitir_I_Come_Completely_from_the_Mountains"] + ["núna_lærum_við_um_mánuði_á_íslensku"], play=True)
    num = random.choice(range(1,13))
    say_phrase(["hvernig_segir_maður"] + q_data[num]["eng_toks"] + ["á_íslensku"], play=True, question=True)
    print(generate_buttons(3, word_bank))
    grade_phrase(["þriðji", "mánuðurinn", "er", "mars"], num)
    grade_phrase(["þriðji", "mánuðurinn", "mars", "er"], num)