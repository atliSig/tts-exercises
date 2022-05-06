#! /bin/bash

VOX=my_voice
# Synthesize one example sentence.
python3 ../lvl_is_text/normalize.py tests.txt "-" > noramlized_tests.txt

s_dir=synthesized

if [ -d "$s_dir" ]; then rm -Rf $s_dir; fi
mkdir $s_dir

index=0

# Note: the following is configured to work with unit selection
# Use the following instead in lines 20 and 21
#  -eval festvox/lvl_is_${VOX}_cg.scm \
#  -eval "(voice_lvl_is_${VOX}_cg)" \
cat noramlized_tests.txt | while read line || [[ -n $line ]]
do
  echo $line |
  ../festival/bin/text2wave \
  -eval festvox/lvl_is_${VOX}_clunits.scm \
  -eval "(voice_lvl_is_${VOX}_clunits)" \
  > $s_dir/example_$index.wav

  ((index=index+1))
done

