import PySimpleGUI as sg
import iccftm
import random
from PIL import Image
import io

question_num = random.choice(range(1,13))
button_words = ['play'] * 8

def get_img_data(f, maxsize=(500, 300)):
    """
    Generate image data using PIL
    """
    img = Image.open(f)
    img.thumbnail(maxsize)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()


section1 = [[sg.Titlebar('Mánuði á íslensku')],
            [sg.Text('Hæ og velkomin í tungumálaforritið sem heitir I Come Completely from the Mountains', key='-TRANSCRIPT-', font=('helvetica', '20'))],
            [sg.Text('Núna lærum við um mánuði á íslensku', key='-TRANSCRIPT2-', font=('helvetica', '20'))],
            [sg.Text('')],
            [sg.Button(button_words[0],  button_color='blue on yellow', key = 'button1'),
             sg.Button(button_words[1], button_color='blue on yellow', key = 'button2'),
             sg.Button(button_words[2], button_color='blue on yellow', key = 'button3'),
             sg.Button(button_words[3], button_color='blue on yellow', key = 'button4')],
            [sg.Button(button_words[4],  button_color='blue on yellow', key = 'button5'),
             sg.Button(button_words[5], button_color='blue on yellow', key = 'button6'),
             sg.Button(button_words[6], button_color='blue on yellow', key = 'button7'),
             sg.Button(button_words[7], button_color='blue on yellow', key = 'button8')],
            [sg.Input(key='-IN-'), sg.Button('Submit')]
             ]


layout =   [
            #### Section 1 part ####
            [section1],
            ##### Image ####
            [sg.Image(key='-image-', data=get_img_data('./images/mountain.png'))],
            #### Buttons at bottom ####
            [sg.Button('New question'), sg.Button('Exit')]]

sg.SetOptions(font=('helvetica', '20'))
window = sg.Window('I Come Completely from the Mountains', layout, size=(800,600))

def gen_new_question():
    window['-IN-']('')
    global question_num
    question_num = random.choice(range(1,13))
    window['-TRANSCRIPT-'](' '.join(["Hvernig segir maður"] + [x.replace('_', ' ') for x in iccftm.q_data[question_num]["eng_toks"]] + ["á íslensku?"]))
    window['-TRANSCRIPT2-']('')
    button_words = iccftm.generate_buttons(question_num, iccftm.word_bank)
    for i, button in enumerate(['button1', 'button2', 'button3', 'button4', 'button5', 'button6', 'button7', 'button8']):
        window[button](button_words[i])
    window['-image-'](data=get_img_data('./images/{}-Number-PNG.png'.format(question_num)))
    iccftm.say_phrase(["Hvernig_segir_maður"] + iccftm.q_data[question_num]["eng_toks"] + ['á_íslensku'], play=True, question=True)
start = True

while True:             # Event Loop
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if start == True:
        iccftm.say_phrase(["hæ_og_velkomin_í_tungumálaforritið_sem_heitir_I_Come_Completely_from_the_Mountains"], play=True)
        iccftm.say_phrase(["núna_lærum_við_um_mánuði_á_íslensku"], play=True)
        start = False
        gen_new_question()
    elif event.startswith('button'):
        window['-IN-'](window.Element('-IN-').get() + ' ' + window.Element(event).GetText())
        iccftm.say_phrase([window.Element(event).GetText()], play=True)
    if event == 'New question':
        gen_new_question()
    if event == 'Submit':
        submission = window['-IN-'].get()
        feedback = iccftm.grade_phrase(submission.split(), question_num)
        window.Element('-TRANSCRIPT-').update(' '.join([x.replace('_', ' ') for x in feedback[0]]))
        window.Element('-TRANSCRIPT2-').update(' '.join([x.replace('_', ' ') for x in feedback[1]]))
        iccftm.say_phrase(feedback[0], play=True)
        iccftm.say_phrase(feedback[1], play=True)

window.close()
