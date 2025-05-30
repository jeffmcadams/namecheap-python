"""Shell completion support for the Namecheap CLI."""


def get_completion_script(shell: str) -> str:
    """Generate completion script for the specified shell."""
    if shell == "bash":
        return """
# Bash completion for nc (Namecheap CLI)
_nc_completion() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD \
        _NC_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY+=("$value/")
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY+=("$value")
            compopt -o filenames
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=("$value")
        fi
    done

    return 0
}

_nc_completion_setup() {
    complete -o nosort -F _nc_completion nc
    complete -o nosort -F _nc_completion namecheap
}

_nc_completion_setup
"""
    if shell == "zsh":
        return """
# Zsh completion for nc (Namecheap CLI)
_nc_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[nc] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) \
        _NC_COMPLETE=zsh_complete nc)}")

    for type key descr in ${response}; do
        if [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        elif [[ "$type" == "dir" ]]; then
            _path_files -/
        elif [[ "$type" == "file" ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _nc_completion nc
compdef _nc_completion namecheap
"""
    if shell == "fish":
        return """
# Fish completion for nc (Namecheap CLI)
function _nc_completion
    set -l response (env COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) \
        _NC_COMPLETE=fish_complete nc)

    for completion in $response
        set -l metadata (string split "," $completion)

        if test $metadata[1] = "dir"
            __fish_complete_directories $metadata[2]
        else if test $metadata[1] = "file"
            __fish_complete_path $metadata[2]
        else if test $metadata[1] = "plain"
            echo $metadata[2]
        end
    end
end

complete -c nc -f -a "(_nc_completion)"
complete -c namecheap -f -a "(_nc_completion)"
"""
    raise ValueError(f"Unsupported shell: {shell}")
