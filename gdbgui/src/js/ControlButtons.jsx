import React from "react";

import Actions from "./Actions.js";
import FileOps from "./FileOps.jsx";
import GdbApi from "./GdbApi.jsx";
import { store } from "statorgfc";

class ControlButtons extends React.Component {
  constructor() {
    super();
    store.connectComponentState(this, [
      "gdb_pid",
      "fullname_to_render",
      "aceEditor"
    ]);
  }
  render() {
    let btn_class = "btn btn-default btn-sm";

    return (
      <React.Fragment>
        <button
          id="flash_button"
          onClick={() => this.click_flash_button()}
          type="button"
          title="Compile and Flash program"
          className={btn_class}
        >
          <span className="glyphicon glyphicon-download-alt" />
        </button>

        <button
          id="run_button"
          onClick={() => GdbApi.click_run_button()}
          type="button"
          title="Reset program and halt"
          className={btn_class}
        >
          <span className="glyphicon glyphicon-repeat" />
        </button>

        <button
          id="continue_button"
          onClick={() => GdbApi.click_continue_button()}
          type="button"
          title={
            "Continue until breakpoint is hit or inferior program exits keyboard shortcut: c" +
            (initial_data.rr ? ". shift + c for reverse." : "")
          }
          className={btn_class}
        >
          <span className="glyphicon glyphicon-play" />
        </button>

        <button
          onClick={() =>  GdbApi.click_pause_button()}
          type="button"
          title="Send Interrupt signal (SIGINT) to gdb process to pause it and allow interaction with it"
          className={btn_class}
        >
          <span className="glyphicon glyphicon-pause" />
        </button>

        <button
          id="step_button"
          onClick={() => GdbApi.click_step_button()}
          type="button"
          title={
            "Step" +
            (initial_data.rr ? ". shift + s for reverse." : "")
          }
          className={btn_class}
        >
          <span className="glyphicon glyphicon-arrow-down" />
        </button>

      </React.Fragment>
    );
  }
  click_flash_button() {
    debugger
    let pid = this.state.gdb_pid
    let code = store.get("aceEditor").getSession().getValue();
    if (code.length > 0)
      Actions.compile_and_flash(pid, code);
      
  }
}

export default ControlButtons;
