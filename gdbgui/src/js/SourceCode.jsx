/**
 * A component to render source code, assembly, and break points
 */

import { store } from "statorgfc";
import React from "react";
import FileOps from "./FileOps.jsx";
import Breakpoints from "./Breakpoints.jsx";
import Memory from "./Memory.jsx";
import MemoryLink from "./MemoryLink";
import constants from "./constants.js";
import Actions from "./Actions.js";

import AceEditor from "react-ace";

import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools"
import "ace-builds/src-noconflict/mode-assembly_x86.js";

class SourceCode extends React.Component {
  static el_code_container = null; // todo: no jquery
  static el_code_container_node = null;
  static code_container_node = null;
  static view_more_top_node = null;
  static view_more_bottom_node = null;

  constructor() {
    super();
    this.markers = [];
    store.connectComponentState(this, [
      "fullname_to_render",
      "cached_source_files",
      "missing_files",
      "disassembly_for_missing_file",
      "line_of_source_to_flash",
      "paused_on_frame",
      "breakpoints",
      "source_code_state",
      "make_current_line_visible",
      "source_code_selection_state",
      "current_theme",
      "inferior_binary_path",
      "source_linenum_to_display_start",
      "source_linenum_to_display_end",
      "max_lines_of_code_to_fetch",
      "source_code_infinite_scrolling"
    ]);
  }

  render() {
    return (
      <div className={this.state.current_theme} style={{ height: "100%" }}>
        <AceEditor
          ref='aceEditor'
          placeholder=""
          mode="assembly_x86"
          theme="github"
          name=""
          fontSize={16}
          width={ '100%' }
          height={ '100%' }
          showPrintMargin={true}
          showGutter={true}
          highlightActiveLine={true}
          value={this.get_body()}
          markers={this.markers}
          setOptions={{
            enableBasicAutocompletion: true,
            enableLiveAutocompletion: true,
            enableSnippets: true,
            showLineNumbers: true,
            tabSize: 2,
          }}
        />
      </div>
    );
  }

  componentDidMount() {
    this.refs.aceEditor.editor.on("guttermousedown", (evt) => this.updateBreakpoints(evt));
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    const bkpt_lines = Breakpoints.get_breakpoint_lines_for_file(
      this.state.fullname_to_render
    )
    const editor = this.refs.aceEditor.editor
    editor.session.clearBreakpoints();
    const breakpoints = editor.session.getBreakpoints(row, 0);

    for (let row of bkpt_lines) 
      if(typeof breakpoints[row] === typeof undefined) 
        editor.session.setBreakpoint(row - 1, 'ace_breakpoint');  
    let line_gdb_is_paused_on = this.state.paused_on_frame
      ? parseInt(this.state.paused_on_frame.line)
      : 0;
    editor.resize(true);
    editor.scrollToLine(line_gdb_is_paused_on, true, true, function () {});
  }

  updateBreakpoints(e) {
    const target = e.domEvent.target;
    if (target.className.indexOf("ace_gutter-cell") == -1) {
        return;
    }
    const row = e.getDocumentPosition().row + 1;

    Breakpoints.add_or_remove_breakpoint(this.state.fullname_to_render, row);
    e.stop();
  }

  get_body() {
    const states = constants.source_code_states;
    switch (this.state.source_code_state) {
      case states.ASSM_AND_SOURCE_CACHED: // fallthrough
      case states.SOURCE_CACHED: {
        let obj = FileOps.get_source_file_obj_from_cache(this.state.fullname_to_render);
        if (!obj) {
          console.error("expected to find source file");
          return this.get_body_empty();
        }
        let line_gdb_is_paused_on = this.state.paused_on_frame
          ? parseInt(this.state.paused_on_frame.line)
          : 0;
        this.markers = []
        this.markers.push({startRow: line_gdb_is_paused_on - 1, endRow: line_gdb_is_paused_on, className: 'replacement_marker', type: 'text' });
        return obj.source_code_obj.join('\n');
      }
      case states.FETCHING_SOURCE: {
        return "Fetching source, please wait";
      }
      case states.ASSM_CACHED: {
        return "Assembly fetched";
      }
      case states.FETCHING_ASSM: {
        return "Fetching assembly, please wait";
      }
      case states.ASSM_UNAVAILABLE: {
        return "Cannot access address";
      }
      case states.FILE_MISSING: {
        return `File not found: ${this.state.fullname_to_render}`;
      }
      case states.NONE_AVAILABLE: {
        return this.get_body_empty();
      }
      default: {
        console.error("developer error: unhandled state");
        return this.get_body_empty();
      }
    }
  }
  get_body_empty() {
    return "";
  }
}

export default SourceCode;
