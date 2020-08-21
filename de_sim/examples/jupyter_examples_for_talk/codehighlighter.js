define([
    'base/js/namespace'
], function(
    Jupyter
) {
    function load_ipython_extension() {

        var style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = '.codehighlighter { background: yellow; }';
        document.getElementsByTagName('head')[0].appendChild(style);

        var highlight_code_in_cell = function (cell, from, to) {
            var cm = cell.code_mirror;
            for ( var lineno = from; lineno < to ; ++lineno )
                cm.addLineClass(lineno, 'background', 'codehighlighter');
        }

        var highlight_selected_code = function () {
            var cell = Jupyter.notebook.get_selected_cell();
            var cm = cell.code_mirror;
            var from = cm.getCursor('from');
            var to = cm.getCursor('to');
            var endLine = (to.ch > 0 ? to.line + 1 : to.line);
            highlight_code_in_cell(cell, from.line, endLine);
            if ( ! cell.metadata.codehighlighter )
                cell.metadata.codehighlighter = [];
            cell.metadata.codehighlighter.push([from.line, endLine]);
        };

        var highlight_from_metadata = function() {
            Jupyter.notebook.get_cells().forEach(function(cell) {
                if (cell.metadata.codehighlighter) {
                    cell.metadata.codehighlighter.forEach(function(range) {
                        highlight_code_in_cell(cell, range[0], range[1]);
                    });
                }
            });
        }

        function registerAction(action_name, action) {
            var prefix = 'codehighlighter';
            return Jupyter.actions.register(action, action_name, prefix);
        }

        var hilite_code = registerAction('highlight-code', {
                                         icon: 'fa-lightbulb-o',
                                         help    : 'Highlight selected code',
                                         help_index : 'zz',
                                         handler : highlight_selected_code
        });
        var restore_hilites = registerAction('restore-highlights', {
                                         icon: 'fa-bars',
                                         help    : 'Restore highlights',
                                         help_index : 'zz',
                                         handler : highlight_from_metadata
        });

        Jupyter.toolbar.add_buttons_group([hilite_code, restore_hilites]);
    }

    return {
        load_ipython_extension: load_ipython_extension
    };
});
