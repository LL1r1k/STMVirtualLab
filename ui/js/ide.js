let editor;

window.onload = function() {
    ace.require("ace/ext/language_tools");
    editor = ace.edit("editor");
    editor.setTheme("ace/theme/monokai");
    editor.session.setMode("ace/mode/c_cpp");

    editor.setOptions({
        enableBasicAutocompletion: true,
        enableSnippets: true,
        enableLiveAutocompletion: true
    });
}

function changeLanguage() {
    let language = $("#languages").val();

    if(language == 'c')editor.session.setMode("ace/mode/c_cpp");
    else if(language == 'assembler')editor.session.setMode("ace/mode/assembly_x86");
}

function executeCode() {
    $.ajax({
        url: "/app/compiler.php",
        method: "POST",
        data: {
            language: $("#languages").val(),
            code: editor.getSession().getValue()
        },
        success: function(response) {
            $(".output").text(response)
        }
    })
}