# Final Project
The final project is an opportunity for you to reflect on the work you have achieved in the course so far and for you to demonstrate the power of your TTS models.

You will turn in a short document, 3-5 pages, that describes your design decisions, the process of creating the models and the results from your MOS survey.

In most cases, you can use the results and text you have already generated in your previous assignments to complete the final project. But remember that it is always good to add your own comments and insights.

You should turn in a PDF made in a text editor, e.g. LaTeX, Office Word, Google Docs. The document should contain a front page with your name and a title. It should then contain the following sections.

## Introduction and Background
**(maximum 500 words)**
* A description of what TTS is and the general process ofmaking    TTS models: i.e. collecting text and speech data,training models,    etc.
* Brief description on what we aim to achieve in script design,w.   r.t. unit selection TTS, and why it is important
* Describe what we want in our recordings w.r.t. quality, prosody,    etc.
* Brief description of Festival in general
* Brief description of unit selection in general.
* Brief description of the Clustergen TTS and how it is different from unit selection.

## Experimental Setup
**(maximum 500 words)**
* Script Design:
    * A description of your coverage algorithm
    * What units you decided to cover
* The Dataset:
    * If you recorded your own data: describe your recording setup
    * If not: general information about the dataset.
    * Everyone: how did you trim the recordings, manually or automatically? If automatically, describe the method you used
* Describe the recipe you used for the three different TTS models (or which steps are performed in these recipes):
    * Unit selection in Festival (steps)
    * Clustergen in Festival (steps)

## Results
* Script Design:
    * Include any plots you may have generated
    * State the coverage you achieve
* The Dataset:
    * clearly state the threshold you used to trim the recordings.
    * The scatter plot for assignment 5.
    * Show a waveform plot for at least one of your recordings and the corresponding text

    If you didn't record your own data, then also include:

    * The coverage of your new dataset
    * The waveform trim plots you did in assignment 5
* MOS and comparisons: Include results from the MOS assignment. Specifically, for each group (Festival, Ground truth) do the following:
    * What is the average MOS score for each sample and across all samples in the group.
    * Create a bar chart with a bar for each rating value (1-5) and set the height as the corresponding number of responses for the given value.
    * Create a plot with sample index on the x-axis and MOS score on the y-axis where you plot the graph of each participant's MOS response to  each question (on the same graph).
    * The ratio of samples that were completely understood (the words are the same in the input and the survey)

    Also comment on the following:
    * Your thoughts on the quality and nature of the two different Festival TTS models and in which way they sound different.

## Conclusions
* Comment on which of the models you prefer and why. Put this into context with the amount of data that you trained on.
* How could you improve the models?
