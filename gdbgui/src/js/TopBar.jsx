import React from "react";

import { store } from "statorgfc";
import BinaryLoader from "./BinaryLoader.jsx";
import ControlButtons from "./ControlButtons.jsx";
import Settings from "./Settings.jsx";
import SourceCodeHeading from "./SourceCodeHeading.jsx";
import ToolTipTourguide from "./ToolTipTourguide.jsx";
import FileOps from "./FileOps.jsx";
import GdbApi from "./GdbApi.jsx";
import Actions from "./Actions.js";
import constants from "./constants.js";
import Util from "./Util.js";

let onkeyup_jump_to_line = e => {
  if (e.keyCode === constants.ENTER_BUTTON_NUM) {
    Actions.set_line_state(e.currentTarget.value);
  }
};


let show_license = function () {
  Actions.show_modal(
    "gdbgui license",
    <React.Fragment>
      <a href="https://github.com/cs01/gdbgui/blob/master/LICENSE">
        GNU General Public License v3.0
      </a>
      <p>Copyright © Chad Smith</p>
      <p>This software can be used personally or commercially for free.</p>
      <p>
        Permissions of this strong copyleft license are conditioned on making available
        complete source code of licensed works and modifications, which include larger
        works using a licensed work, under the same license. Copyright and license notices
        must be preserved. Contributors provide an express grant of patent rights.
      </p>
      <p>
        If you wish to redistribute gdbgui as part of a closed source product, you can do
        so for a fee. Contact grassfedcode@gmail.com for details.
      </p>
    </React.Fragment>
  );
};

let About = {
  show_about: function () {
    Actions.show_modal(
      "About gdbgui",
      <React.Fragment>Copyright © Chad Smith, grassfedcode.com</React.Fragment>
    );
  }
};

let show_session_info = function () {
  Actions.show_modal(
    "session information",
    <React.Fragment>
      <table>
        <tbody>
          <tr>
            <td>gdb version: {store.get("gdb_version")}</td>
          </tr>

          <tr>
            <td>gdb pid for this tab: {store.get("gdb_pid")}</td>
          </tr>
        </tbody>
      </table>
    </React.Fragment>
  );
};

const menu = (
  <ul
    style={{ height: 25, padding: 0, paddingRight: "15px", fontSize: "1.3em" }}
    className="nav navbar-nav navbar-right"
  >
    <li id="menudropdown" className="dropdown">
      <a
        href="#"
        data-toggle="dropdown"
        role="button"
        style={{ height: 25, padding: 0, paddingRight: 20 }}
        className="dropdown-toggle"
      >
        <span className="glyphicon glyphicon-menu-hamburger"> </span>
      </a>
      <ul className="dropdown-menu">
        <li>
          <a title="dashboard" className="pointer" href="/dashboard">
            Dashboard
          </a>
        </li>
        <li>
          <a
            title="show guide"
            className="pointer"
            onClick={ToolTipTourguide.start_guide}
          >
            Show Guide
          </a>
        </li>
        <li>
          <a onClick={show_session_info} className="pointer">
            Session Information
          </a>
        </li>

        <li role="separator" className="divider" />
        <li>
          <a href="https://github.com/cs01/gdbgui" className="pointer">
            GitHub
          </a>
        </li>
        <li>
          <a href="http://gdbgui.com" className="pointer">
            Homepage
          </a>
        </li>

        <li>
          <a href="https://www.youtube.com/channel/UCUCOSclB97r9nd54NpXMV5A">
            YouTube Channel
          </a>
        </li>

        <li role="separator" className="divider" />
        <li>
          <a onClick={show_license} className="pointer">
            License
          </a>
        </li>
        <li>
          <a onClick={About.show_about} className="pointer">
            About gdbgui
          </a>
        </li>
      </ul>

      <ToolTipTourguide
        top={"100%"}
        left={"-300px"}
        step_num={0}
        content={
          <div>
            <h5>Welcome to gdbgui.</h5>
            <p>
              This guide can be shown at any time by clicking the menu button,
              <span className="glyphicon glyphicon-menu-hamburger"> </span>, then clicking
              "Show Guide".
            </p>
          </div>
        }
      />
    </li>
  </ul>
);

class TopBar extends React.Component {
  constructor() {
    super();
    // state local to the component
    this.state = {
      assembly_flavor: "intel", // default to intel (choices are 'att' or 'intel')
      show_spinner: false
    };
    // global state attached to this component
    store.connectComponentState(
      this,
      [
        "debug_in_reverse",
        "source_code_state",
        "waiting_for_response",
        "show_filesystem",
        "latest_gdbgui_version",
        "gdbgui_version"
      ],
      this.store_update_callback.bind(this)
    );

    this.spinner_timeout = null;
    this.spinner_timeout_msec = 5000;
  }
  store_update_callback(keys) {
    if (keys.indexOf("waiting_for_response") !== -1) {
      this._clear_spinner_timeout();
      this.setState({ show_spinner: false });
      if (this.state.waiting_for_response === true) {
        // false to true
        this._set_spinner_timeout();
      }
    }
  }
  _set_spinner_timeout() {
    this.spinner_timeout = setTimeout(() => {
      if (this.state.waiting_for_response) {
        this.setState({ show_spinner: true });
      }
    }, this.spinner_timeout_msec);
  }
  _clear_spinner_timeout() {
    clearTimeout(this.spinner_timeout);
  }
  toggle_assembly_flavor() {
    const flavor = this.state.assembly_flavor === "att" ? "intel" : "att";
    this.setState({ assembly_flavor: flavor });
    GdbApi.set_assembly_flavor(flavor);
    Actions.clear_cached_assembly();
    FileOps.fetch_assembly_cur_line();
  }
  get_controls() {
    return (
      <div
        role="group"
        style={{ marginBottom: 12, marginLeft: 6,marginRight: 6, marginTop: 6, height: 25,}}
        className="btn-group btn-group"
      >
        <ToolTipTourguide
          step_num={3}
          position={"bottomleft"}
          onClick={e => e.stopPropagation()}
          content={
            <div>
              <h5>
                These buttons allow you to control execution of the target you are
                debugging.
              </h5>
              <p>
                Hover over these buttons to see a description of their action. For
                example, the <span className="glyphicon glyphicon-repeat" /> button starts
                (or restarts) a program from the beginning.
              </p>
              <p>
                Each button has a keyboard shortcut. For example, you can press "r" to
                start running.
              </p>
            </div>
          }
        />
        <ControlButtons />
      </div>
    );
  }
  render() {
    let toggle_assm_button = "";
    if (
      this.state.source_code_state ===
      constants.source_code_states.ASSM_AND_SOURCE_CACHED ||
      this.state.source_code_state === constants.source_code_states.ASSM_CACHED
    ) {
      toggle_assm_button = (
        <button
          onClick={this.toggle_assembly_flavor.bind(this)}
          type="button"
          title={"Toggle between assembly flavors. The options are att or intel."}
          className={"btn btn-default btn-xs"}
        >
          <span
            title={`Currently displaying ${this.state.assembly_flavor}. Click to toggle.`}
          >
            {this.state.assembly_flavor}
          </span>
        </button>
      );
    }

    let reload_button_disabled = "disabled";
    if (
      this.state.source_code_state ===
      constants.source_code_states.ASSM_AND_SOURCE_CACHED ||
      this.state.source_code_state === constants.source_code_states.SOURCE_CACHED
    ) {
      reload_button_disabled = "";
    }
    let reload_button = (
      <button
        onClick={FileOps.refresh_cached_source_files}
        type="button"
        title="Erase file from local cache and re-fetch it"
        className={"btn btn-default btn-xs " + reload_button_disabled}
      >
        <span>reload file</span>
      </button>
    );

    let spinner = (
      <span className="" style={{ height: "100%", margin: "5px", width: "14px" }} />
    );
    if (this.state.show_spinner) {
      spinner = (
        <span
          className="glyphicon glyphicon-refresh glyphicon-refresh-animate"
          style={{ height: "100%", margin: "5px", width: "14px" }}
        />
      );
    }

    let reverse_checkbox = null;
    if (initial_data.rr) {
      reverse_checkbox = (
        <label
          title={
            "when clicking buttons to the right, pass the `--reverse` " +
            "flag to gdb in an attempt to debug in reverse. This is not always supported. " +
            "rr is known to support reverse debugging. Keyboard shortcuts go in " +
            "reverse when pressed with the shift key."
          }
          style={{ fontWeight: "normal", fontSize: "0.9em", margin: "5px" }}
        >
          <input
            type="checkbox"
            checked={store.get("debug_in_reverse")}
            onChange={e => {
              store.set("debug_in_reverse", e.target.checked);
            }}
          />
          reverse
        </label>
      );
    }

    return (
      <div
        id="top"
        style={{ background: "#f5f6f7", position: "absolute", width: "100%" }}
      >
        <div className="flexrow">
          <div
            style={{ marginRight: "0", marginLeft: "10px", marginTop: "4px" }}
          >
          <a class="btn btn-default" href="/">Главная страница</a>
          </div>
          {this.get_controls()}
          <div
            id="menu"
            style={{ marginRight: "0", marginLeft: "auto", marginTop: "10px" }}
          >
            <span
              onClick={() => Settings.toggle_key("show_settings")}
              title="settings"
              className="pointer glyphicon glyphicon-cog"
              style={{ marginRight: "10px", fontSize: "1.3em" }}
            />
          </div>
        </div>
      </div>
    );
  }
  static needs_to_update_gdbgui_version() {
    // to actually check each value:
    try {
      return Util.is_newer(
        store.get("latest_gdbgui_version"),
        store.get("gdbgui_version")
      );
    } catch (err) {
      console.error(err);
      return true;
    }
  }
}

export default TopBar;
