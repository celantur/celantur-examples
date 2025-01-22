import Queue from 'yocto-queue';
import path from 'path';
import fs from 'fs';
import { pipeline } from 'stream/promises';

const TASKS_PER_AUTHENTICATION = 50; // Number of tasks before re-authentication
const SLEEP_TIME = 10000; // ms wait time between querying request
const MAX_CHECK_STATUS = 1000; // Retry 1000 times to check status before stopping
const EXTENSIONS = ['.jpg', '.jpeg', '.png'];

export class CelanturClientParameters {
    constructor(
        input, 
        output, 
        username, 
        password, 
        configuration, 
        endpoint,  
        recursive,
        fileType) {

        this.input = input;
        this.output = output;
        this.username = username;
        this.password = password;
        this.configuration = configuration;
        this.endpoint = endpoint;
        this.recursive = recursive;
        this.fileType = fileType;
    }

}

export class CelanturCloudAPIClient {
    // constructor fields
    #inputQueue = new Queue(); // queue of filepaths to process
    #authToken;
    #totalCount = 0; 
    #inputFolder;
    #outputFolder;
    #username;
    #password;
    #configFilePath;
    #endpoint;
    #recursive;
    #fileType;
    
    // init. fields on run()
    #config;
    #dottedExtensions;
    #ENDPOINT_LOGIN;
    #ENDPOINT_TASK;


    constructor(params) {
        if (!params.input || !params.output || !params.username || !params.password || !params.configuration) {
            throw Error("Missing required arguments: input, output, username, password or configuration.");
        }
        this.#inputFolder = params.input;
        this.#outputFolder = params.output;
        this.#username = params.username;
        this.#password = params.password;
        this.#configFilePath = params.configuration;
        this.#endpoint = params.endpoint !== undefined ? params.endpoint : 'https://api.celantur.com/v2/';
        this.#recursive = params.recursive !== undefined ? params.recursive : true;
        this.#fileType = params.fileType;
    }
    
    async run() {
        // setup based on args
        this.#dottedExtensions = this.normalizeExtensions(this.#fileType);
        this.#config = await this.readConfigurationFile();

        this.#endpoint = this.#endpoint.replace(/\/$/, ''); //remove trailing slash (if any)
        this.#ENDPOINT_LOGIN = `${this.#endpoint}/signin/`;
        this.#ENDPOINT_TASK = `${this.#endpoint}/task/`;

        await this.getFilesWithoutOverwriteFrom(this.#inputFolder, this.#outputFolder, this.#recursive, this.#dottedExtensions);

        this.#authToken = await this.authenticate();
        const startTime = Date.now();
        const processingTasks = [];
        while (this.#inputQueue.size !== 0) {
            processingTasks.push(this.runTask(this.#inputQueue.dequeue()));
        }

        Promise.all(processingTasks).then(() => {
            const endTime = Date.now();
            console.info(
                `Completed. It took ${Math.floor((endTime - startTime) / 1000)} seconds (${Math.floor((endTime - startTime) / 60000)} minutes)`
            );
        });
    }

    async runTask(taskFile) {
        const taskData = await this.createTask();
        taskData.input_file_path = path.join(taskFile.rootInputPath, taskFile.relFilePath);
        taskData.output_file_path = path.join(this.#outputFolder, taskFile.relFilePath);
        
        if (await this.uploadImage(taskData)) {
            await this.downloadImage(taskData);
            this.#totalCount++;
    
            if (this.#totalCount % TASKS_PER_AUTHENTICATION == 0) this.#authToken = await this.authenticate(); // re-authenticate
        }
    
    }

    async loadImage(path) {
        try {
          const buffer = await fs.promises.readFile(path);
          console.log(`Image loaded: ${path}`);
          return buffer;    
        } catch (err) {
          console.error('Error reading image: ', err);
          throw err;
        }
    }
    
    async uploadImage(task) {
        const img = await this.loadImage(task.input_file_path);
        
        const response = await fetch(task.upload_url, {
            method: 'PUT',
            body: img
        });
        if (!response.ok) {
            throw new Error(`Image upload failed (Status ${response.status_code}): ${response.text}`);
        }
    
        console.log(`Uploaded image ${task.input_file_path} successfully.`);
        return true;
      }
    
    
    async downloadImage(task) {
        let counter = 1;
        let taskStatus;
        while (counter < MAX_CHECK_STATUS) {
            taskStatus = await this.getTaskStatus(task.task_id);
            if (taskStatus === 'done') {
                break;
            }
            console.log(`[Retry ${counter}/${MAX_CHECK_STATUS}] Status: ${taskStatus}, sleeping ${SLEEP_TIME} ms...`);
            counter++;
            await new Promise(r => setTimeout(r, SLEEP_TIME));
        }
    
        if (taskStatus != 'done') {
            console.log(`The task ${task.task_id} did not finish in time.`)
        } else {
            const taskResponse = await this.getTask(task.task_id);
            const anonymizedUrl = taskResponse.anonymized_url;
            const response = await fetch(anonymizedUrl);
            
            const dir = path.dirname(task.output_file_path);
            try { // check if dir exists (if not, create)
                await fs.promises.access(dir);
            } catch (err) {
                if (err.code === 'ENOENT') {
                    await fs.promises.mkdir(dir, { recursive: true });
                } else {
                    throw err;
                }
            }
            await pipeline(response.body, fs.createWriteStream(task.output_file_path));
    
            console.info(`[image ${this.#totalCount}] Anonymized image ${task.output_file_path} received.`);
            console.info(`Task ${task.task_id} completed.`);
        }
    }
    
    
    async getTaskStatus(id) {
        const response = await fetch(`${this.#ENDPOINT_TASK}${id}/status`, {
        method: 'GET',
        headers: { 'Authorization': this.#authToken}
        });
        
        if (!response.ok) {
            throw new Error(`Getting task status failed (Status ${response.status_code}): ${response.text}`);
        }
        const responseBody = await response.json(); 
        console.log(`Task ${id} has status: ${responseBody.task_status}`);
        return responseBody.task_status;
    }
    
    async getTask(id) {
        const response = await fetch(`${this.#ENDPOINT_TASK}${id}`, {
        method: 'GET',
        headers: {'Authorization': this.#authToken}
        });
        
        if (!response.ok) {
            throw new Error(`Getting task failed (Status ${response.status_code}): ${response.text}`);
        }
        console.info(`GET /task/${id} successful.`);
        const responseBody = await response.json(); 
        return responseBody;
    }
    
    async readConfigurationFile() {
        try {
            const data = await fs.promises.readFile(this.#configFilePath, 'utf8');
            return JSON.parse(data);
        } catch (err) {
            console.error('Error reading the file:', err);
        }
    }
    
    // Ensure that the file extensions start with a dot and are lowercase.
    normalizeExtensions(extensions) {
        if (!extensions || extensions.length === 0) {
            return EXTENSIONS;
        }
        else {
            let dottedExtensions = [];
            for (let e of extensions) {
                let lowercase = e.toLowerCase()
                if (!lowercase.startsWith('.')) {
                    lowercase = '.' + lowercase;
                }
                if (!EXTENSIONS.includes(lowercase)) {
                    throw new Error(`File type ${lowercase} not supported!`);
                } else {
                    dottedExtensions.push(lowercase);
                }
            }
            return dottedExtensions;
        }
    }
    
    async *getFilesFrom(rootPath, relativePath, extensions, recursive) {
        const dirPath = path.join(rootPath, relativePath);
    
        try {
            const files = await fs.promises.readdir(dirPath);
            
            for (const file of files) {
                const filePath = path.join(dirPath, file);
                const stat = await fs.promises.stat(filePath);
                
                if (stat.isFile() && extensions.includes(path.extname(file).toLowerCase())) {
                    yield path.join(relativePath, file);
                } else if (recursive && stat.isDirectory()) {
                    yield* this.getFilesFrom(rootPath, path.join(relativePath, file), extensions, recursive);
                }
            }
        } catch (err) {
            console.error(err);
            process.exit(-1);
        }
    }
    
    async getFilesWithoutOverwriteFrom(rootInputPath, rootOutputPath, recursive, extensions) {
        for await (const relFilePath of this.getFilesFrom(rootInputPath, '', extensions, recursive)) {
            const outputPath = path.join(rootOutputPath, relFilePath);
            
            try {
                const outputExists = await fs.promises.access(outputPath).then(() => true).catch(() => false);
                
                if (outputExists) {
                    console.log(`Skip ${relFilePath} because ${outputPath} already exists.`);
                } else {
                    this.#inputQueue.enqueue({rootInputPath: rootInputPath, 
                        relFilePath: relFilePath});
                        console.log(`Put into file queue: ${relFilePath}`);
                    }
                } catch (err) {
                console.error(`Error checking file: ${err.message}`);
            }
        }
    }
    
    async authenticate() {
        const data = {
            username: this.#username,
            password: this.#password
        };
    
        try {
            const response = await fetch(this.#ENDPOINT_LOGIN, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`Login error (Status ${response.status}): ${await response.text()}`);
            }
    
            const responseBody = await response.json();
            const authToken = responseBody.AccessToken;
    
            console.info('Successfully authenticated and token received.');
            return authToken;
        } catch (err) {
            console.error(err.message);
            process.exit(-1);
        }
    }
    
    async createTask() {
        const response = await fetch(this.#ENDPOINT_TASK, {
            method: 'POST',
            headers: { 'Authorization': this.#authToken },
            body: JSON.stringify(this.#config)
        });
        if (!response.ok) {
            throw new Error(`Creating task failed (Status ${response.status}): ${await response.text()}`);
        }
    
        const responseBody = await response.json();
        console.log(`Task ${responseBody.task_id} created`);
        return responseBody;
    }
}