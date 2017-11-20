#! /usr/bin/python
"""
    Python Volume Threshold Detector
"""

import pyaudio
import audioop
import sys
import time
import operator

class ThresholdDetector():
    p = pyaudio.PyAudio()

    def __init__(self, chunk=512, audio_format='paInt16', channels=1, volume_threshold=None,
                 time_threshold=3.5, frames=1024, recording_sample=0.25, op=operator.lt,
                 detector='timed'):
        """ initialize the detector
        """

        detectors = {
            'simple': self.simple_detector,
            'timed': self.timed_volume_detector
        }
        self.chunk                  = chunk # the size of an individual data chunk when sampling
        self.format                 = getattr(pyaudio, audio_format) # audio file format
        self.volume_threshold       = volume_threshold # the value of the volume threshold
        self.time_threshold         = time_threshold # the value of the 
        self.sample_rate            = 44100 # number of bytes per second
        self.frames                 = frames # number of frames per buffer
        self.recording_sample       = recording_sample # number of seconds to sample from
        self.stream                 = None # the PyAudio stream
        self.alerted_threshold      = False 
        self.was_at_threshold       = False
        self.threshold_timestamp    = None  # time value set when a detector determines the volume is below the set threshold.
        self.operator               = op
        try:
            self.detector           = detectors[detector]
        except ValueError:
            raise Exception("Detectors must be: simple or timed")
        self.set_device_info()
        self.create_stream()
        if volume_threshold is None:
            self.set_volume_threshold()

    def set_volume_threshold(self, test_time=5, multiplier=2):
        """ streams sound for 5 seconds and then sets volume threshold
            to slightly more than the 3rd highest recorded volume
        """
        self.stdout('Sampling volume to reset threshold. Please be silent...')
        self.stdout('3\n2\n1\nSampling...')
        start_time = time.time()
        volumes = []
        while time.time() - start_time < test_time:
            volume = self.get_volume()
            volumes.append(volume)
            self.stdout('current volume is {}'.format(volume))

        volumes.sort()
        threshold = sum(volumes) / len(volumes) * multiplier
        self.stdout('volume threshold set at: {}'.format(threshold))
        self.volume_threshold = threshold

    def set_device_info(self, index=None):
        """
            sets the input device
            index - int: set
            p.get_default_input_device returns a dictionary like this:
            { 'defaultSampleRate': 44100.0,
              'defaultLowOutputLatency': 0.01,
              'defaultLowInputLatency': 0.00199546485260771,
              'maxInputChannels': 2L,
              'structVersion': 2L,
              'hostApi': 0L,
              'index': 0L, 
              'defaultHighOutputLatency': 0.1,
              'maxOutputChannels': 0L,
              'name': u'Built-in Microph',
              'defaultHighInputLatency': 0.012154195011337868 }
        """
        try:
            if index is None or not isinstance(index, int):
                self.device = self.p.get_default_input_device_info()
            else:
                self.device = self.p.get_device_info_by_index(index)
        except IOError:
            raise "No input device found -- can't proceed"

    def create_stream(self, ):
        """ Create pyaudio stream object
        """
        self.stream = self.p.open(format=self.format,
                                  channels=int(self.device['maxInputChannels']),
                                  rate=int(self.device['defaultSampleRate']),
                                  input=True,
                                  frames_per_buffer=self.frames,
                                  input_device_index=int(self.device['index']))

    def get_volume(self, ):
        """ reads sample data and calculates volume
            the stream's sample rate is the number of bytes per second
            To go from raw data to volume, this function
            splits the sample time into a number of raw data chunks (iterations)
            and then calculates the root mean square for each chunk of
            raw data, yielding a list of values which are then averaged
            to get one volume value for the entire sample
        """ 
        volumes = []
        iterations = int(self.device['defaultSampleRate'] / self.chunk * self.recording_sample)
        
        for _ in xrange(0, iterations):
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            volumes.append(audioop.rms(data, 2)) # calculates the root mean square of the signal's sine wave
        return sum(volumes) / len(volumes)

    def detect_volume_threshold(self, average):
        """ checks the volumes relationship to the threshold
            (greater than or less than) given user settings
        """
        return self.operator(average, self.volume_threshold)


    def detect_time_threshold(self, ):
        """ checks if the difference between the current time and
            the time at which the stream activated the threshold
            is greater than the preset time threshold

        """
        if self.threshold_timestamp:
            return time.time() - self.threshold_timestamp > self.time_threshold
        return False

    def stdout(self, output):
        """ prints in a way node will detect
        """
        sys.stdout.flush()
        sys.stdout.write(str(output) + '\n')
        sys.stdout.flush()

    def simple_detector(self, ):
        """ Reads volumes from input audio stream and prints 0 if 
            volume is below the threshold, otherwise prints 1
        """
        while True:
            average = self.get_volume()
            is_below_threshold = self.detect_volume_threshold(average)
            if is_below_threshold:
                self.stdout(0)
            else:
                self.stdout(1)
    
    def timed_volume_detector(self, ):
        """ Reads volumes from input audio stream and
            alerts if time and volume thresholds are exceeded
        """
        while True:
            average = self.get_volume()
            is_below_threshold = self.detect_volume_threshold(average)
            above_time_threshold = self.detect_time_threshold()
            self.stdout(average)
            if is_below_threshold and above_time_threshold and not self.alerted_threshold:
                self.stdout('Time and volume thresholds met!')
                self.alerted_threshold = True
            elif is_below_threshold and not self.was_at_threshold:
                self.stdout('New threshold period, counting down time threshold')
                self.was_at_threshold = True
                self.threshold_timestamp = time.time()
            elif not is_below_threshold and self.was_at_threshold and self.alerted_threshold:
                self.stdout('Seconds thresholds were met: {}'.format(time.time() - self.threshold_timestamp))
                self.alerted_threshold = False
                self.was_at_threshold = False
                self.threshold_timestamp = None
            elif not is_below_threshold:
                self.was_at_threshold = False
                self.threshold_timestamp = None

    def run(self, ):
        """ runs user set threshold detector
        """
        time.sleep(1)
        self.detector()

if __name__ == "__main__":
    sys.stdout.flush()
    argv_len = len(sys.argv)
    if argv_len > 5:
        sys.stdout.write('Usage: ./threshold_detector.py [detector] [volume_threshold] [time_threshold] [operator]')
        sys.exit(1)

    options = {}
    if argv_len > 1:
        options['detector'] = sys.argv[1].lower()
        if options['detector'] not in ('simple', 'timed'):
            sys.stdout.write('Please indicate whether detector is simple or timed\n')
            sys.exit(1)

    if argv_len > 2:
        try:
            options['volume_threshold'] = float(sys.argv[2])
        except ValueError:
            sys.stdout.write('Please provide a number for the volume threshold\n')
            sys.exit(1)

    if argv_len > 3:
        try:
            options['time_threshold'] = float(sys.argv[3])
        except ValueError:
            sys.stdout.write('Please provide a number for the time threshold\n')
            sys.exit(1)
    
    if argv_len > 4:
        try:
            options['op'] = operator.gt if sys.argv[4].lower() == 'gt' else operator.lt
        except:
            sys.stdout.write('No valid operator given\n')
            sys.exit(1)

    sd = ThresholdDetector(**options)
    sd.run()