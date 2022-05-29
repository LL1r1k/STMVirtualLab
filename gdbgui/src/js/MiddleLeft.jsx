/**
 * The middle left div will be rendered with this content
 */

import React from "react";
import SourceCode from "./SourceCode.jsx";
import FileOps from "./FileOps.jsx";
// import AceEditor from "react-ace";

// import "ace-builds/src-noconflict/theme-github";
// import "ace-builds/src-noconflict/ext-language_tools"
// import "ace-builds/src-noconflict/mode-assembly_x86.js";

class MiddleLeft extends React.Component {
  constructor() {
    super();
    this.onscroll_container = this.onscroll_container.bind(this);
    this.onscroll_timeout = null;
    this.fetch_more_at_top_timeout = null;
  }
  render() {
    // return (
    //   <div
    //     id="code_container"
    //     ref={el => (this.source_code_container_node = el)}
    //   >
    //     <AceEditor
    //       placeholder=""
    //       mode="assembly_x86"
    //       theme="github"
    //       name=""
    //       fontSize={16}
    //       width={ '100%' }
    //       height={ '100vh' }
    //       showPrintMargin={true}
    //       showGutter={true}
    //       highlightActiveLine={true}
    //       setOptions={{
    //         enableBasicAutocompletion: true,
    //         enableLiveAutocompletion: true,
    //         enableSnippets: true,
    //         showLineNumbers: true,
    //         tabSize: 2,
    //       }}
    //     />
    //   </div>
    // );
    
    return (
      <div
        id="code_container"
        style={{ overflow: "auto", height: "100%" }}
        ref={el => (this.source_code_container_node = el)}
      >
        <SourceCode />
      </div>
    );
  }
  componentDidMount() {
    SourceCode.el_code_container = $("#code_container"); // todo: no jquery
    
    if (this.source_code_container_node) {
      this.source_code_container_node.onscroll = this.onscroll_container.bind(this);
    }
  }

  onscroll_container() {
    clearTimeout(this.onscroll_timeout);
    this.onscroll_timeout = setTimeout(this.check_to_autofetch_more_source, 100);
  }

  check_to_autofetch_more_source() {
    // test if "view more" buttons are visible, and if so, fetch more source

    let fetching_for_top = false; // don't fetch for more at bottom and top at same time
    if (SourceCode.view_more_top_node) {
      let { is_visible } = SourceCode.is_source_line_visible(
        $(SourceCode.view_more_top_node)
      );
      if (is_visible) {
        fetching_for_top = true;
        FileOps.fetch_more_source_at_beginning();
      }
    }

    if (!fetching_for_top && SourceCode.view_more_bottom_node) {
      let { is_visible } = SourceCode.is_source_line_visible(
        $(SourceCode.view_more_bottom_node)
      );
      if (is_visible) {
        FileOps.fetch_more_source_at_end();
      }
    }
  }
}

export default MiddleLeft;
