import Yargs from 'yargs/yargs';
import { hideBin } from 'yargs/helpers';
import { CelanturCloudAPIClient } from './cloud-api-v2-client.js';

// this script allows you to run the client from the terminal and pass in options

const argv = Yargs(hideBin(process.argv))
.usage('Usage: $0 -i [input] -o [output] -u [username] -p [password]')
.options({
    input: {
        alias: 'i',
        describe: 'Input folder containing images',
        type: 'string',
        demandOption: true,
    },
    output: {
        alias: 'o',
        describe: 'Output folder for saving anonymized images',
        type: 'string',
        demandOption: true,
    },
    username: {
        alias: 'u',
        describe: 'Username for Celantur Cloud API',
        type: 'string',
        demandOption: true,
    },
    password: {
        alias: 'p',
        describe: 'Password for Celantur Cloud API',
        type: 'string',
        demandOption: true,
    },
    configuration: {
        alias: 'c',
        describe: 'Anonymisation configuration as JSON file',
        type: 'string',
        demandOption: true,
    },
    endpoint: {
        alias: 'e',
        describe: 'Celantur Cloud API v2 endpoint',
        type: 'string',
        default: 'https://api.celantur.com/v2/',
    },
    recursive: {
        describe: 'Recursively go through the input folder',
        type: 'boolean',
        default: true,
    },
    fileType: {
        describe: 'Select file type to anonymize',
        type: 'array',
    },
})
.help()
.alias('help', 'h')
.argv;

let client = new CelanturCloudAPIClient(argv)
client.run();        
