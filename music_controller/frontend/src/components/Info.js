import React, { useState, useEffect } from "react";
import { Grid, Button, Typography, IconButton } from "@material-ui/core";
import NavigateBeforeIcon from "@material-ui/icons/NavigateBefore";
import NavigateNextIcon from "@material-ui/icons/NavigateNext";
import { Link } from "react-router-dom";

//create a sort of enum to clarify pages
const pages = {
  JOIN: "pages.join",
  CREATE: "pages.create",
};


// this is a functional component.
// better and more natural than class components
export default function Info(props) {
  // state variable! it has the name and the function to update the name. It is equal to the initialized value
  // state variable to keep tracks of the info page I am on
  const [page, setPage] = useState(pages.JOIN);

  //to define functions you just nest them one inside the component :)
  function joinInfo() {
    return "Join page";
  }

  function createInfo() {
    return "Create page";
  }


  //useEffect replace componentDidMount, componentWillMount and componentWillUnmount
  // so to update the song every second (in room) we would have used useEffect
  useEffect(() => {
    //ran every time the components mounts or updates!
    console.log("ran");

    //if we want to use componentWillUnmount
    // we clean up every time we update, not mounting
    //so to unmount just use the return function
    return () => console.log("cleanup");
  });

  return (
    <Grid container spacing={1}>
      <Grid items xs={12} align="center">
        <Typography component="h4" variant="h4">
          What is House Party ?
        </Typography>
      </Grid>
      <Grid item xs={12} align="center">
        <Typography variant="body1">
          {page === pages.JOIN ? joinInfo() : createInfo()}
        </Typography>
      </Grid>
      <Grid item xs={12} align="center">
        <IconButton
          onClick={() => {
            page === pages.CREATE ? setPage(pages.JOIN) : setPage(pages.CREATE);
          }}
        >
          {page === pages.CREATE ? (
            <NavigateBeforeIcon />
          ) : (
            <NavigateNextIcon />
          )}
        </IconButton>
      </Grid>
      <Grid item xs={12} align="center">
        <Button color="secondary" variant="contained" to="/" component={Link}>
          Back
        </Button>
      </Grid>
    </Grid>
  );
}
