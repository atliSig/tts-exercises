# Present Your Results

At the end of the course, you will present your results to the class.

The role of the presentation is not to go deep into how the TTS models you have trained work since we would
then listen to the same presentation from every student.

## The Layout

The presentation should pretty much be an overview of the *Experimental Setup* and *Results* sections of your final project report.

The list below is basically a copy of that from the report README. You don't have to follow it, it's put here to give you a rough feeling for how expansive the presentation should be.

**The presentation should be no longer than 10 minutes**

1. Reading List
    * A description of your coverage algorithm
    * What units you decided to cover
    * Include any plots you may have generated
    * State the coverage you achieve
2. The Dataset
    * If you recorded your own data: describe your recording setup
    * Everyone: how did you trim the recordings, manually or automatically? If automatically, describe the method you used
    * state the threshold you used to trim the recordings.
    * The scatter plot for assignment 5.
    * Show a waveform plot for at least one of your recordings and the corresponding text

    If you didn't record your own data, then also include:

    * The coverage of your new dataset
    * The waveform trim plots you did in assignment 5

3. Results and MOS

    Include results from the MOS assignment. Specifically, for each group (Festival, Ossian, Ground truth) do the following:
    * What is the average MOS score for each sample and across all samples in the group.
    * Create a bar chart with a bar for each rating value (1-5) and set the height as the corresponding number of responses for the given value.
    * Create a plot with sample index on the x-axis and MOS score on the y-axis where you plot the graph of each participant's MOS response to  each question (on the same graph).
    * The ratio of samples that were completely understood (the words are the same in the input and the survey)

    Also comment on the following:

    * Your thoughts on the quality and nature of the two different Festival TTS models and in which way they sound different.
    * Compare the results of training only on a subset of your dataset and the complete dataset using the Ossian recipe.
    * Error plots for the Ossian recipe.

## Play samples
Most importantly, we want to listen to your TTS. You can show off as many samples as you think you can fit into your presentation. In my opinion, it is both very interesting and fun to listen to bad synthesis samples that give you an idea about the limitations of your TTS. Don't worry about the quality too much.


## Presenting Remotely
We will not present at the University. Instead I have decided to use [Google Meet](https://meet.google.com/). Why do I prefer Google Meet over Microsoft Teams? Google Meet offers a pretty easy way of sharing sysem audio in a presentation which is kinda important in this case. Therefore you should:
* Create a Google Slides presentation since it's key to present via the browser.
* To embed audio in your presentation, press `Insert` and select `audio`.
* I will send you a link to the Google Meet session, open it in Google Chrome.
* When it is your turn to present during the Google Meet session:
    1. Have your presentation open in a seperate Google Chrome window.
    2. Click `present now`
    3. Select `A chrome tab`
    4. Select the tab that contains your presentation.
    5. Make sure that the `Presentation Audio` is set to on inside the Google Meet session.


