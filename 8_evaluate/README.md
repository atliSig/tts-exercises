# Evaluate your TTS
It is time to evaluate your TTS systems. We will use the very popular MOS (Mean Opinion Score) metric for this task. In a MOS test a participant:
* Listens to multiple synthesized waveforms
* The participant rates each on a scale from 1 to 5, 1 being "completely unnatural" and 5 being "completely natural"

It is hard to judge exactly what participants are rating in MOS but there is evidence that the participants often base their score on how much they like the system, rather than how much they actually understand of what was being said. We will add two modifications to the MOS metric to get additional information:
1. We will ask the participants to write down what words they heard.
2. We will sprinkle in some ground truth waveforms (i.e. some recordings from your training data) to attempt to ground the ratings.

## Google Drive and Google Forms
We will be using Google Forms to carry out this task. An example MOS survey is available [here](https://docs.google.com/forms/d/1KsEq-Ckt_z1oHAnlWWl_h07NhkqJCUMRHZkZPGPVKlM/edit?usp=sharing). To the best of my knowledge, there is no direct way to embed audio in google form. I just added the waveforms to a public Google Drive folder and add links to each waveform in each question. You can do the same. You can use this Google form as a template for your survey.

## Technical details
In your form you should survey:
* 10 synthesized samples from your Festival TTS (you can choose to **either** use your unit selection voice **or** your clustergen voice)
* 10 synthesized samples from your Ossian TTS
* 5 ground truth samples
Randomize the order of these so not do add unwanted bias. Make sure that the text being read is different in each sample, otherwise we could also add unwanted bias.

You should ask 5 individuals to complete your MOS survey. Jón and I will also do your surveys so send us your link.

## What to Turn In
It is enough for you to simply turn in a link to your MOS survey. You should also complete which is a part of the final project:
You should report on the results in a short document. For each group (Festival, Ossian, Ground truth) do the following:
* What is the average MOS score for each sample and across all samples in the group.
* Create a bar chart with a bar for each rating value (1-5) and set the height as the corresponding number of responses for the given value.
* Visualize, in your own selected way, how the individual participants respond to each question in your survey (e.g. plotting the MOS response as a function of the question index).
* The ratio of samples that were completely understood (the words are the same in the input and the survey)