/**
 * The middle left div will be rendered with this content
 */

import React from "react";
import SourceCode from "./SourceCode.jsx";
import FileOps from "./FileOps.jsx";

class MiddleLeft extends React.Component {
  constructor() {
    super();
  }
  render() {    
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
    
  }
}

export default MiddleLeft;
