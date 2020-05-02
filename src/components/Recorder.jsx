import React from "react";
import { default as TheRecorder } from "recorder-js";

export default class Recorder extends React.Component {
  constructor(props) {
    super(props);
    const audioContext = new (window.AudioContext ||
      window.webkitAudioContext)();
    this.recorder = new TheRecorder(audioContext, {
      // An array of 255 Numbers
      // You can use this to visualize the audio stream
      // If you use react, check out react-wave-stream
      // onAnalysed: (data) => console.log(data),
    });

    let isRecording = false;
    let blob = null;
  }

  componentDidMount() {
    window.navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => this.recorder.init(stream))
      .catch((err) => console.log("Uh oh... unable to get stream...", err));
  }

  startRecording = () => {
    this.recorder.start().then(() => (isRecording = true));
  };

  stopRecording = () => {
    this.recorder.stop().then(({ blob, buffer }) => {
      console.log(blob);
      console.log(buffer);

      // buffer is an AudioBuffer
    });
  };

  render() {
    return (
      <div>
        recorder
        <br />
        <button onClick={startRecording}>record</button>
        <button onClick={stopRecording}>stop</button>
      </div>
    );
  }
}
