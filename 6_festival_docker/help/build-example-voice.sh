#! /bin/bash

set -o errexit
set -o pipefail
set -o nounset

if [ "$(ls | wc -l)" != 0 ] ; then
  echo "Voice building should probably be done in an empty directory."
  echo "The current directory $(pwd) is not empty."
  echo "Press ^C to abort, or RET to proceed if you know what you're doing."
  read
fi

set -v

VOX=anon_example

# Set up the Festvox Clustergen build:
$FESTVOXDIR/src/clustergen/setup_cg lvl is $VOX

# Unpack the wave files into the ./wav directory:
unzip ${VOX}.zip 1> unzip.log 2>unzip.err

# Convert to 16KHz, single channel, 16 bit
for i in audio/*/*.wav
do
	sox "$i" -r 16000 -c 1 -b 16 "wav/$(basename -s .wav "$i").wav" 1> sox.log 2> sox.err
done

# Configure a 16kHz voice:
sed -i 's/^(set! framerate .*$/(set! framerate 16000)/' festvox/clustergen.scm

# Set up the prompts that we will train on.
# Create transcriptions
python3 ../lvl_is_text/normalize.py info.json txt.complete.data --lobe --scm

# Add string in front of promt names
# (Festival doed not seem to handle names that start with a number)
sed -i 's/( [^\.]*\./( is/' txt.complete.data
rename 's/wav\/[^\.]*\./wav\/is/' wav/*.wav

# Filter out prompts with numbers or a 'c' since we don't have a proper normalizer
grep -v '"[^"]*[0-9c]' txt.complete.data > txt.nonum.data

# This could either be the full set of prompts:
cp -p txt.nonum.data etc/txt.done.data

# Or it could be a subset of prompts:
#head -n100 txt.nonum.data > etc/txt.done.data

# Create a lexicon:

#Create list of all words in prompts
python3 ../lvl_is_text/normalize.py info.json "-" --lobe | grep -o "[^ ]*" | sort | uniq > vocabulary.txt

cp ../lvl_is_text/framburdarordabok.txt lexicon.txt

# copy the G2P model from the data directory:
wget https://eyra.ru.is/ttsdatawebstoragefolder/ipd_clean_slt2018.mdl
# or if this fails you will have to train your own:
# g2p.py --train lexicon.txt --devel 50% --write-model model-1 1> g2p-1.log 2>g2p-1.err
# and replace the --model parameter below with model-1
g2p.py --model ipd_clean_slt2018.mdl --apply vocabulary.txt --encoding utf-8 > lexicon-prompts.txt

# Create a compiled scm lexicon from lexicon
python3 ../lvl_is_text/build_lexicon.py ../lvl_is_text/aipa-map.tsv lexicon.txt lexicon.scm
python3 ../lvl_is_text/build_lexicon.py ../lvl_is_text/aipa-map.tsv lexicon-prompts.txt lexicon-prompts.scm

#Combine multiple scm lexicons
echo "MNCL" > festvox/lexicon.scm
cat lexicon.scm lexicon-prompts.scm | fgrep "(" | sort | uniq >> festvox/lexicon.scm

# Adjust various configuration files based on the phonology description:
../lvl_is_text/apply_phonology.py ../lvl_is_text/phonology.json .

# Run the Festvox Clustergen build. This can take several minutes for every 100
# training prompts. Total running time depends heavily on the number of CPU
# cores available.
time bin/build_cg_voice 1>build.out 2>build.err

# Synthesize one example sentence.
echo 'halló _pause ég kann að tala íslensku alveg hnökralaust' |
../festival/bin/text2wave \
  -eval festvox/lvl_is_${VOX}_cg.scm \
  -eval "(voice_lvl_is_${VOX}_cg)" \
  > example.wav
