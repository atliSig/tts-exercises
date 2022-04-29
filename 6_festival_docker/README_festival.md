# Festival

## 1. About Festival
*The following is built on the [official Festival documentation](http://www.festvox.org/)*

Festival is a general multi-lingual speech synthesis system. The system is written in C++ and uses the Edinburgh Speech Tools Library for low level architecture and has a Scheme (SIOD) based command interpreter for control.

We will now quickly cover the three basic parts of TTS in Festival:
### 1-2. Text & Linguistic Analysis
*From raw text to identified words and basic utterances. Then finding pronunciations of the words and assigning prosodic structure to them: phrasing, intonation and durations.*

Text analysis is the task of identifying the *words* in the text. By *words*, we mean tokens for which there is a well defined method of finding their pronunciation, i.e. from a lexicon, or using letter-to-sound rules.

The first task in text analysis is to make chunks out of the input text (tokenizing it). In Festival, at this stage,

we also chunk the text into more reasonably sized *utterances*. An utterance structure is used to hold the information for what might most simply be described as a sentence. Separating a text into utterances is important, as it allows synthesis to work bit by bit, allowing the waveform of the first utterance to be available more quickly than if the whole files was processed as one.

Apart from chunking, text analysis also does *text normalization*. There are many tokens which appear in text that do not have a direct relationship to their pronunciation. Numbers are perhaps the most obvious example. Consider the following sentence

"*On May 5 1996, the university bought 1996 computers.*"

In English, tokens consisting of solely digits have a number of different forms of pronunciation.
* The "*5*" above is pronounced "*fifth*", an ordinal, because it is the day in a month
* The first "*1996*" is pronounced as "*nineteen ninety six*" because it is a year
* the second "*1996*" is pronounced as "*one thousand nine hundred and ninety six*" (British English) as it is a quantity.

Two problems that turn up here: non-trivial relationship of tokens to words, and homographs, where the same token may have alternate pronunciations in different contexts. In Festival, homograph disambiguation is considered as part of text analysis. In addition to numbers, there are many other symbols which have internal structure that require special processing; such as money, times, addresses, etc. All of these can be dealt with in Festival by what is termed *token-to-word rules*. These are of course language specific.

#### Lexicons
After we have a set of words to be spoken, we have to decide what the sounds should be; what phonemes, or basic speech sounds, are spoken. Each language and dialect has a phoneme set associated with it. Given a set of units we can train models from them, but it is up to linguistics to help us find good levels of structure and the units at each.

#### Prosody
Prosody, or the way things are spoken, is an extremely important part of the speech message. Changing the placement of emphasis in a sentence can change the meaning of a word, and this emphasis might be revealed as a change in pitch, volume, voice quality, or timing.

We'll present two approaches to taming the prosodic beast:
* limiting the domain to be spoken
* intonation modeling.

By limiting the domain, we can collect enough data to cover the whole output. For some things, like weather or stock quotes, very high quality can be produced, since these are rather contained.

For general synthesis, however, we need to be able to turn any text, or perhaps concept, into a spoken form, and we can never collect all the sentences anyone could ever say. To handle this, we break the prosody into a set of features, which we predict using statistically trained models:
* phrasing
* duration
* intonation
* energy
* voice quality

### 3. Waveform Generation
*From a fully specified form (pronunciation and prosody) generate a waveform.*

For the case of concatenative synthesis, we actually collect recordings of voice talent, and this captures the voice quality to some degree. This way, we avoid detailed physical simulation of the oral tract, and perform synthesis by integrating pieces that we have in our inventory; as we don't have to produce the precisely controlled articulatory motion, we can model the speech using the units available in the sound alone

During waveform generation, the system assembles the units into an audio file or stream, and that can be finally "*spoken*". There can be some distortion as these units are joined together, but the results can also be quite good.

We systematically collect the units, in all variations, so as to be able to reproduce them later as needed. To do this, we design a set of utterances that contain all of the variation that produces meaningful or apparent contrast in the language, and record it (You did a naive version of this in assignment 4).



## 2. About the Recipe
The recipe you will run uses the  [Clustergen training method](https://www.cs.cmu.edu/~awb/papers/is2006/IS061394.PDF) that is included in Festival. Clustergen is a *statistical parametric synthesis* (SPS) system. SPS systems do not select units from a database like unit selection systems but generate the waveform directly by training statistical parametric models.

### About Clustergen
1. **Label the database**:

    The first stage, which is not technically part of the clustergen synthesizer is to label the database using an HMM labeler. Clustergen uses EHMM which is included within the latest FestVox release. It uses Baum Welch from a flat start to train context independent HMM models, which it then uses to force align the phonemes generated from the transcriptions with the audio.

    Clustergen uses 3-state models, that generate HMM state sized labels, three per phone.

2. **Extract features**:
    F0 is extracted using the Edinburgh Speech Tools `pda` program. Using the generated phoneme labels, the F0 is interpolated through unvoiced regions, thus there is a non-zero F0 value for all 5ms frames that contain voiced or unvoiced speech.

    24 MFCCs are combined with the F0 to give a 25 feature vector every 5ms. For each of these vectors high level features are extracted, including phone context (with phonetic features), syllable structure, word position, etc.

3. **Training feature predictors**:
    Clustering is done by the Edinburgh Speech Tools CART tree builder `wagon`. CART trees are built with `wagon` to find questions that split the data to minimize impurity. A tree is built for all the vectors labeled with the same HMM state name.

    Separate F0 and MFCC models are built. No delta features are used in clustergen.

    An additional CART tree is built to predict durations for each HMM state. Each state duration is predicted independently.

4. **Synthesis**:
    At synthesis time the phone string is generated from the text as is done in other synthesis techniques within Festival, then an HMM
    state name relation is build linking each phone to its three subphonetic parts.

    The duration CART tree is used to predict the length of each HMM state. A set of empty vectors is created to fill the length of the predicted state duration. Using the CART tree specific to the state name, the questions are asked and the means from the vector at the selected leaf are added as values to each vector.

    After prediction smoothing is done by a simple 3-point moving average to each track of coefficients.

    Then the speech is reconstructed from the predicted parameters using the MLSA filter. Voicing decisions are currently done by phonetic type directly from the labels, rather than trained from the acoustics.



### Technical overview of the `build-voice.sh` script
All the steps to train the model are performed inside `/usr/local/src/lvl_is_txt/build-voice.sh` in the Docker image. The main steps in the voice building script are:

1. Setup the Festvox Clustergen build:

        $FESTVOXDIR/src/clustergen/setup_cg lvl is $VOX

    * `$FESTVOXDIR` is an environment variable that points to `/usr/local/src/festvox/`
    * `$VOX` is the identify of the voice. This could for example be `atli`. The demo recipe supports `$VOX=f1` or `$VOX=m1` where `f1` is a female voice and `m1` is a male voice.

2. The script will download the voice data that you have selected (f1 or m1):

        wget https://eyra.ru.is/ttsdatawebstoragefolder/${VOX}-small.zip

3. We then convert the voice data to the right format, 16 bit single channel at 16 kHz:

        for i in audio/*/*.wav
        do
            sox "$i" -r 16000 -c 1 -b 16 "wav/$(basename -s .wav "$i").wav" 1\
            > sox.log 2> sox.err
        done

4. Configure the clustergen voice:

        sed -i 's/^(set! framerate .*$/(set! framerate 16000)/' festvox/clustergen.scm

5. Normalize the prompts for the recordings using `lvl_text/normalize.py` which can read in the `info.json` file that is exported from sLOBE:

        python3 ../lvl_is_text/normalize.py info.json "-" --lobe | grep -o "[^ ]*" | sort | uniq > vocabulary.txt

    Most importantly, the normalizer will:
    * lower case all text
    * remove punctuations and other symbols such as "!", ";" and ":".
    * Replace certain symbols with a `_pause` token to denote a pause in speech. Specifically we only replace "," with a pause.

    **You can change this normalization script if you like but make sure to document your changes.**


6. Since this naive recipe does not have a very advanced normalizer for Icelandic we have to remove some sentences (specifically that contain numbers or the character "c" which appear in some of the prompts on sLOBE). You might need to edit this rule if you run into issues:

        grep -v '"[^"]*[0-9c]' txt.complete.data > txt.nonum.data

7. Select sentences to train on. This could either be the full set of prompts:

        cp -p txt.nonum.data etc/txt.done.data

    or a subset, below we use `head -n1000` to select the first 1000 prompts from `txt.nonum.data`:

        head -n1000 txt.nonum.data > etc/txt.done.data

8. Next we create the Festival lexicon. It is an specific scheme format and must contain pronounciations for all words that appear in the training data:
    1. First copy all words from the training data

            python3 ../lvl_is_text/normalize.py info.json "-" --lobe | grep -o "[^ ]*" | sort | uniq > vocabulary.txt

    2. Copy the lexicon from `lvl_is_text/`:

            cp ../lvl_is_text/framburdarordabok.txt lexicon.txt

    3. Apply a pretrained Sequitur G2P model to words in training data

            wget https://eyra.ru.is/ttsdatawebstoragefolder/ipd_clean_slt2018.mdl
            g2p.py --model ipd_clean_slt2018.mdl --apply vocabulary.txt --encoding utf-8 > lexicon-prompts.txt

    4. Create a combined lexicon

            python3 ../lvl_is_text/build_lexicon.py ../lvl_is_text/aipa-map.tsv lexicon.txt lexicon.scm
            python3 ../lvl_is_text/build_lexicon.py ../lvl_is_text/aipa-map.tsv lexicon-prompts.txt lexicon-prompts.scm
            echo "MNCL" > festvox/lexicon.scm
            cat lexicon.scm lexicon-prompts.scm | fgrep "(" | sort | uniq >> festvox/lexicon.scm

    5. Apply the phonology script which reads a phonology description and writes/updates several files in a Festvox Clustergen build tree, including the phonset definition and various feature and feature description files:

            ../lvl_is_text/apply_phonology.py ../lvl_is_text/phonology.json .

9. Run the Clustergen build:

        time bin/build_cg_voice 1>build.out 2>build.err

10. After training, synthesize one sample and save it to `./example.wav`

        echo 'halló _pause ég kann að tala íslensku alveg hnökralaust' |
        ../festival/bin/text2wave \
        -eval festvox/lvl_is_${VOX}_cg.scm \
        -eval "(voice_lvl_is_${VOX}_cg)" \
        > example.wav

    TODO: this assumes that no preprocessing is applied to the input (which won't be the case in the end).

## 3. Testing the Festival recipe
We will start by testing the recipe on pre-recorded data.

1. Under `/usr/local/src/`, create a new directory: `mdkir demo_voice`.
2. Direct your shell to the new directory: `cd demo_voice`
3. Do e.g. `export VOICE=f` if you want to train on the female voice data.
4. Select the number of training prompts. Select a low value for fast (but worse) results. Replace:

        head -n1000 txt.nonum.data > etc/txt.done.data

   with

        head -n100 txt.nonum.data > etc/txt.done.data

   to train on only 100 prompts.

5. Run the `build-voice.sh` script via `../lvl_is_text/build-voice.sh`

The script will now perform all of the steps that were mentioned above and this could take some time to finish. To get an idea about what Festival is doing, you can write the `build.out` stream to the terminal window:
* Open a new terminal window
* do `tail -f demo_voice/build.out`

If everything went as expected you should have seen a lot of stuff printed in the terminal and a new `example.wav` file should have appeared with an example synthesis sample.

## 4. Creating Your Own Clustergen Voice
We will now train the TTS on your own data.

### Prepare the Data
The recipe expects that you include at least the `audio` directory and `info.json` from the the sLOBE dataset export. Before copying your data, do the following:
1. Make sure that you have trimmed your recordings, either using the manually recorded timestamps or by using `Librosa`.
2. Create a **new** voice building directory under `/usr/local/src` in the container, e.g. `my_voice`.
3. Create a `.zip` archive that contains `audio` and `info.json` at the top level of the `.zip` (i.e. `audio` and `info.json` are the only files or directories that should be in your `.zip`)
4. Now move your `.zip` over to the voice building directory. This is relatively easy using VSC. You can simply:
    * right click a file/folder on your OS, select `copy`
    * right click the voice building directory in your attached container in VSC and select `paste`.
    * This can take some time, wait a couple of minutes and you should see that your data has been copied over. If you don't see anything, press the reload icon in the header of the file explorer in VSC.

If you are not going the VSC route you can use:

        docker cp my_archive.zip <name_of_container>:/usr/local/src/<voice_building_directory>/my_zip.zip

### Change the Recipe
You will have to edit this part of `build-voice.sh` to train on your own data:


        if [ -v VOICE ] && [ $VOICE = "f" ]; then
                VOX=f1
        else
                VOX=m1
        fi
        # Set up the Festvox Clustergen build:
        $FESTVOXDIR/src/clustergen/setup_cg lvl is $VOX

        # Commit the current state of the directory. This will make it easier to see
        # what changed since we ran setup_cg.
        git add --all
        git commit -q -m 'Setup for Clustergen complete.'

        # Unpack the wave files into the ./wav directory:
        #wget https://eyra.ru.is/ttsdatawebstoragefolder/${VOX}-small.zip
        unzip m1-small.zip 1> unzip.log 2>unzip.err

* Create a copy of `build-voice.sh` under `lvl_is_txt` called `custom-voice-build.sh`
* Add execute privilege to the file with `chmod +x custom-voice-build.sh`.
* Replace the code block above with the following block where you have to fill in values wrapped with `<>`:

        VOX=<my_id>
        # Set up the Festvox Clustergen build:
        $FESTVOXDIR/src/clustergen/setup_cg lvl is $VOX

        # Commit the current state of the directory. This will make it easier to see
        # what changed since we ran setup_cg.
        git add --all
        git commit -q -m 'Setup for Clustergen complete.'

        # Unpack the wave files into the ./wav directory:
        unzip <name_of_your_zip>.zip 1> unzip.log 2>unzip.err

### Train on Your Data
It's time to create your clustergen voice! As with the demo data we do the following:
1. Direct your shell to your voice bulding directory, e.g. `my_voice`.
2. Run the custom voice building script with e.g. `../lvl_is_text/custom-voice-build.sh`
3. Wait for results.
4. Refer to the trouble shooting section below if it does not finish.


## 4. Train a Unit Selection Voice

You have now trained an SPS voice, it's time to train a unit selection model. There is very little difference between how we train a unit selection voice and a clustergen voice in Festival.

At `./data/build-unit-selection.sh` you will find a script similar to the `build-voice.sh` in the Docker image. You should:
* Copy this script over to the `lvl_is_text` directory in your container (do `chmod +x <your_script_name>.sh` if needed)
* To avoid having to download everything again, do the following:
    * create a folder called `data` at `/usr/local/src`
    * Copy the `ipd_clean_slt2018.mdl` from your existing voice building directory (or download it via `wget https://eyra.ru.is/ttsdatawebstoragefolder/ipd_clean_slt2018.mdl`) into `data/`
    * Copy your collection `.zip` file into `data/`
* Create a new voice building directory at `usr/local/src` (e.g `my_unit_selection_voice`)
* Change line 16 in `build-unit-selection.sh` to e.g. `VOX=atli.zip` if that's the name of your zip (note: the .zip file can only contain English alphabetical characters)
* Run the unit selection script from there
* Refer to the trouble shooting section below if it does not finish.

## 5. Finishing and what to turn in

Now it's time to generate synthesis samples. All the tools you need are located in the `./data` directory. Do the following:
1. Copy `add_to_lexicon.sh` and `synth_file.sh` from the data directory to your voice building directory. (remember to do `chmod +x` for both of these)
2. Create a list of sentences to synthesize. In assignment 8 you will perform MOS on 10 synthesized samples from your Festival TTS. You should synthesize:
   * The following 10 sentences:
        ```
        Það er greinilegt að vinnu stjórnvalda við breytingar og aðlaganir á aðgerðarpökkunum, til að koma í veg fyrir misnotkun, er hvergi nærri lokið.
        Hnúfubakur er frekar kubbslega vaxinn, sverastur um miðjuna en mjókkar til beggja enda.
        Kona hans, Hulda Jakobsdóttir varð fyrst kvenna bæjarstjóri á Íslandi, en hún tók við bæjarstjórastöðunni af Finnboga.
        Drykkurinn er þekktur á íslensku undir nafninu kók.
        Fönk er tónlistarstefna sem varð til um miðjan sjöunda áratuginn og er nokkurs konar blanda af djassi, blúsi, gospel og sálartónlist.
        Sú tilgáta hefur verið sett fram að Katrín og Hallbera Þorsteinsdóttir séu ein og sama manneskjan.
        Skjálesari er hjálparforrit sem les texta af tölvuskjá upphátt.
        Snara er hugtak í netafræði sem á við legg sem tengir hnút í sjálfan sig.
        Mikki er talandi og manngerð mús sem venjulega klæðist rauðum stuttbuxum, stórum gulum skóm og hvítum hönskum.
        Stutt og laggott.
        ```
    * You will also demonstrate your TTS at the end of the course to us and other students. You can get a good feeling about how your TTS works by testing out *weird* sentences. For example:
        * very short: *Nú?*
        * very long: *Ráðgjafi stjórnvalda í upplýsingarétti telur fátt koma í veg fyrir að birta nöfn stærri fyrirtækja sem sækja fé til ríkisins með hlutabótaleiðinni, enda ætti það að vera opinberar upplýsingar en forstjóri Vinnumálastofnunar segir lítið mál að sjá hvaða einstaklingar séu á bótum ef nöfn lítilla fyrirtækja verða birt, en útilokar ekki nöfn stærri fyrirtækja.*
        * casual: *hahaha, vá það er klikkað!*
        * limited vocabulary: *einn, tveir, þrír, fjórir, fimm, sex, sjö, átta, níu, tíu*

        Test out other 10 sentences of different *types* and look for interesting results to report on in your demonstration. You can quickly *check* a sentence by running the following from within your voice building directory

          export VOX=my_voice
          echo 'mín setning' |
          ../festival/bin/text2wave \
          -eval festvox/lvl_is_${VOX}_clunits.scm \
          -eval "(voice_lvl_is_${VOX}_clunits)" \
          > example.wav
3. Combine this list of 20 sentences into a single file `tests.txt` and place it within your voice building directory.
4. Run `add_to_lexicon.sh`
5. Run `synth_file.sh`
6. Your synthesized samples will now appear in the `synthesized` directory inside your voice building directory.

**Turn In**: Run this for both your Clustergen and Unit Selection voice. Send in the `tests.txt` file and the synthesized samples for both voices.

## Troubleshooting

Your builds might fail and the reason for that should hopefully be written to the `build.err` file in your voice building directory. Here are common build errors that can appear in `build.err`:
* `LEXICON: Word <word> (plus features) not found in lexicon`: The word `<word>` does not appear in the lexicon. If this word is a part of your training prompt then it likely contains invalid characters. If `<word>` is e.g. `quiet` which is invalid because it contains non-Icelandic characters, then you have to change the line

        grep -v '"[^"]*[0-9c]' txt.complete.data > txt.nonum.data

   To make sure you remove all invalid sentences. If you want to also exclude all words that contain "q", change it to e.g.

        grep -v '"[^"]*[0-9cq]' txt.complete.data > txt.nonum.data

* Some thing similar to:

        Cannot open file prompt-utt/is977Z_r000002019_t000002568.utt as tokenstream
        load_utt: can't open utterance input file prompt-utt/is977Z_r000002019_t000002568.utt
        utt.load: loading from "prompt-utt/is977Z_r000002019_t000002568.utt" failed

   There are multiple reasons for why this might happen, a corruption in the recording, a file encoding problem, etc. This hopefully only happens to a subset of your recordings. To fix this, do the following:
   * If it doesn't exist, create a directory called `data/` under `/usr/local/src`
   * Copy your collection .zip over to e.g. a `data/atli/` directory.
   * Unzip your collection zip with e.g. `unzip my_zip.zip`
   * identify the recording ID of the bad recording, above it is `2019` as indicated by `r000002019`. In some datasets it might be `r2019`.
   * Remove the corresponding object from your `info.json` file, i.e. the object that has the key `2019`.
   * Create the new .zip file. From within e.g. `data/atli` do: `zip -r ../atli.zip *`
   * A new `data/atli.zip` should now have appeared.
   * Try building your model again using the new zip file.
