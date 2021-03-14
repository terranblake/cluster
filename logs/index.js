const { appendFileSync } = require('fs');
const tail = require('tail');
const globby = require('globby');
const chokidar = require('chokidar');

const winston = require('winston');
const LogzioWinstonTransport = require('winston-logzio');

const logzioWinstonTransport = new LogzioWinstonTransport({
  level: 'info',
  name: 'winston_logzio',
  token: process.env.LOGZIO_TOKEN,
  host: 'listener.logz.io',
});

const logger = winston.createLogger({
  format: winston.format.simple(),
  defaultMeta: { node: process.env.KUBE_NODE_NAME },
  transports: [logzioWinstonTransport],
});

const FILTERS = process.env.FILTERS;
const EXCLUSIONS = process.env.EXCLUSIONS;

//
// Flag for whether or not logs should be persisted in a file
//
const LOG_TO_FILE =
  (process.env.LOG_TO_FILE &&
    process.env.LOG_TO_FILE === 'true' &&
    process.env.FILENAME !== null) ||
  false;

//
// The log file that the outside world will access
//
const LOGS_FILE = `/logs/${process.env.FILENAME}`;

//
// The directory on the node containing log files.
//
const LOG_FILES_DIRECTORY = '/var/log/containers';

//
// A glob that identifies the log files we'd like to track.
//
const LOG_FILES_GLOB = [
  // Track all log files in the log files diretory.
  `${LOG_FILES_DIRECTORY}/*.log`,
  // Except... don't track logs for Kubernetes system pods.
  `!${LOG_FILES_DIRECTORY}/*kube-system*.log`,
];

//
// List of filters provided from Helm values.yaml to only
// grab log lines from resources that contains 1 of these filters
//
let EXCLUSIVE_FILTERS = (FILTERS && FILTERS.split(' ')) || [];
if (EXCLUSIVE_FILTERS && EXCLUSIVE_FILTERS[0] === '') EXCLUSIVE_FILTERS = [];

const INCLUSIVE_FILTERS =
  (EXCLUSIVE_FILTERS.length > 0 && []) ||
  (EXCLUSIONS && EXCLUSIONS.split(' ')) ||
  [];

//
// Map of log files currently being tracked.
//
const trackedFiles = {};

//
// This function is called when a line of output is received
// from any container on the node.
//
function onLogLine(containerName, line) {
  // The line is a JSON object so parse it first to extract relevant data.
  let data;
  try {
    data = JSON.parse(line);
  } catch (err) {
    if (err) {
      logger.info(`[${containerName}]/[info]`, line);
      return;
    }

    if (typeof data !== 'object') {
      logger.info(
        `[logs]/[error]`,
        `line to output could not be parsed. line ${line}`
      );
      return;
    }
  }
  const isError = data.stream === 'stderr'; // Is the output an error?
  const level = isError ? 'error' : 'info';
  // const timestamp = moment().valueOf();

  const log = `[${containerName}]/[${level}] ${data.log}`;
  logger.info(log);

  if (LOG_TO_FILE === true) appendFileSync(LOGS_FILE, log);
}

//
// Commence tracking a particular log file.
//
function trackFile(logFilePath) {
  const _tail = new tail.Tail(logFilePath);

  // Take note that we are now tracking this file.
  trackedFiles[logFilePath] = _tail;

  // Super simple way to extract the container name from the log filename.
  const [containerPath, namespace, __logName] = logFilePath.split('_');
  const containerPathSegments = containerPath.split('/');
  const containerName = containerPathSegments[containerPathSegments.length - 1];

  for (let filter of INCLUSIVE_FILTERS)
    if (containerName.includes(filter)) return;

  for (let filter in EXCLUSIVE_FILTERS)
    if (!containerName.includes(filter)) return;

  logger.info(
    `[logs]/[info]/[${namespace}] : tracking new log file for container ${containerName} at path ${logFilePath}`
  );

  // Handle new lines of output in the log file.
  _tail.on('line', (line) => onLogLine(containerName, line));

  // Handle any errors that might occur.
  _tail.on('error', (error) => console.error(`ERROR: ${error}`));
}

//
// Identify log files to be tracked and start tracking them.
//
async function trackFiles() {
  const logFilePaths = await globby(LOG_FILES_GLOB);
  for (const logFilePath of logFilePaths) {
    // Start tracking this log file we just identified.
    trackFile(logFilePath);
  }
}

async function main() {
  // Start tracking initial log files.
  await trackFiles();

  // Track new log files as they are created.
  chokidar
    .watch(LOG_FILES_GLOB)
    .on('add', (newLogFilePath) => trackFile(newLogFilePath));
}

main()
  .then(() => logger.info('Online'))
  .catch((err) => {
    console.error('Failed to start!');
    console.error((err && err.stack) || err);
  });
