import React, { Component } from "react";
import { Grid, Button, Typography } from "@material-ui/core";
import CreateRoomPage from "./CreateRoomPage";
import MusicPlayer from "./MusicPlayer";

export default class Room extends Component {
  constructor(props) {
    super(props);
    this.state = {
      votesToSkip: 2,
      guestCanPause: false,
      isHost: false,
      // We want a state variable that tracks if the page is on settings mode or showing mode, so we can render what we need better
      showSettings: false,
      // state variable that checks if spotify is authenticated or not
      spotifyAuthenticated: false,
      song: {},
    };

    // the react router by default the room code in the match prop
    this.roomCode = this.props.match.params.roomCode;

    // bind methods
    this.leaveButtonPressed = this.leaveButtonPressed.bind(this);
    this.updateShowSettings = this.updateShowSettings.bind(this);
    this.renderSettingsButton = this.renderSettingsButton.bind(this);
    this.renderSettings = this.renderSettings.bind(this);
    this.getRoomDetails = this.getRoomDetails.bind(this);
    this.authenticateSpotify = this.authenticateSpotify.bind(this);
    this.getCurrentSong = this.getCurrentSong.bind(this);


    // getting room details
    this.getRoomDetails();
  }

  // Every second we request to spotify an update to the current playing song.
  // So every time every user in the room make a request to spotify
  // Spotify does not support WebSockets, but for ~50000 users shouldbe fine to do all these requests
  componentDidMount() {
    this.interval = setInterval(this.getCurrentSong, 10000);
  }

  componentWillUnmount() {
    // stop making request to spotify
    clearInterval(this.interval);
  }


  getRoomDetails() {
    return fetch("/api/get-room" + "?code=" + this.roomCode)
      .then((response) => {
        if (!response.ok) {
          // see home page for the explanation of the callback
          this.props.leaveRoomCallback();
          this.props.history.push("/");
        }
        return response.json();
      })
      .then((data) => {
        this.setState({
          votesToSkip: data.votes_to_skip,
          guestCanPause: data.guest_can_pause,
          isHost: data.is_host,
        });
        // called after the function execution
        if (this.state.isHost) {
          this.authenticateSpotify();
        }
      });
  }

  // Ask to backend if spotify is authenticated. NEED TO WAIT getRoomDetails
  authenticateSpotify() {
    fetch("/spotify/is-authenticated")
      .then((response) => response.json())
      .then((data) => {
        // change state to if the user is authenticated
        this.setState({ spotifyAuthenticated: data.status });
        console.log(data.status);
        // if user is not authenticated we need to authenticate him
        if (!data.status) {
          fetch("/spotify/get-auth-url")
            .then((response) => response.json())
            .then((data) => {
              // visit the url to authenticate user into his spotify account
              // window.location.replace to redirect in a foreign page
              window.location.replace(data.url);
              // then we will be redirected to the spotify_callback function to save the token
              // then to the frontend
              // then to the correct room we were in
            });
        }
      });
  }

  getCurrentSong() {
    fetch("/spotify/current-song")
      .then((response) => {
        if (!response.ok) {
          return {};
        } else {
          return response.json();
        }
      })
      .then((data) => {
        this.setState({ song: data });
        console.log(data);
      });
  }

  // Before we live the room we need to remove the room code from our session. Check views in API for more info
  leaveButtonPressed() {
    const requestOptions = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    };
    fetch("/api/leave-room", requestOptions).then((_response) => {
      this.props.leaveRoomCallback();
      this.props.history.push("/");
    });
  }

  updateShowSettings(value) {
    this.setState({
      showSettings: value,
    });
  }

  renderSettings() {
    return (
      <Grid container spacing={1}>
        <Grid item xs={12} align="center">
          <CreateRoomPage
            update={true}
            // set the settings form with the current room values
            votesToSkip={this.state.votesToSkip}
            guestCanPause={this.state.guestCanPause}
            roomCode={this.roomCode}
            // this function will be called when we update the room. When we leave the updated room we want to see the changes also in the room page!
            updateCallback={this.getRoomDetails}
          />
        </Grid>
        <Grid item xs={12} align="center">
          <Button
            variant="contained"
            color="secondary"
            onClick={() => this.updateShowSettings(false)}
          >
            Close
          </Button>
        </Grid>
      </Grid>
    );
  }

  // Method returns the html to render the settings button.
  // Created because we want to render the settings button only if the user is the host
  renderSettingsButton() {
    return (
      <Grid item xs={12} align="center">
        <Button
          variant="contained"
          color="primary"
          onClick={() => this.updateShowSettings(true)}
        >
          Settings
        </Button>
      </Grid>
    );
  }

  // ... = spread operator -> divide the keys of a dict and separate them to pass singly
  render() {
    if (this.state.showSettings) {
      return this.renderSettings();
    }
    return (
      <Grid container spacing={1}>
        <Grid item xs={12} align="center">
          <Typography variant="h4" component="h4">
            Code: {this.roomCode}
          </Typography>
        </Grid>
        <MusicPlayer {...this.state.song} />
        {this.state.isHost ? this.renderSettingsButton() : null}
        <Grid item xs={12} align="center">
          <Button
            variant="contained"
            color="secondary"
            onClick={this.leaveButtonPressed}
          >
            Leave Room
          </Button>
        </Grid>
      </Grid>
    );
  }
}
