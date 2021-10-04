#!/usr/bin/env bash
set -e

PARAM1="default-value"

usage() {
PROG="$(basename "$0")"

cat <<EOF
Celantur Bash script template (https://www.celantur.com)
usage: $PROG [options]

  Options:
    -h      Displays help
    -a      Option with argument (default: ${PARAM1})
    -b      Another option with argument (required, no default)
    -c      Flag without argument
EOF
}

while getopts "ha:b:c" flag; do
  case "$flag" in
    h) usage
       exit 0;;
    a) PARAM1=$OPTARG;;
    b) PARAM2=$OPTARG;;
    c) PARAM3=1;;
    *) usage
       exit -1
       ;;
  esac
done

if [[ -z ${PARAM2} ]]; then
  echo "Please provide an argument to -b!"
	exit -1
fi

echo "-a is ${PARAM1}"
echo "-b is ${PARAM2}"
[[ $PARAM3 ]] && echo "-c is set" || echo "-c is not set" 

while 'true'
do
  read -p "Please enter 'yes' or 'no': "
  if [[ ${REPLY//[$'\t\r\n ']} = 'no' ]]
  then
    echo "Operation aborted by customer"
    exit 1
  elif [[ ${REPLY//[$'\t\r\n ']} = 'yes' ]]
  then
    echo "TODO: Logic!"  # Hic sunt dracones
    break
  fi
done



