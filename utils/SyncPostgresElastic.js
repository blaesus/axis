'use strict'
const PostgresPromise = require('pg-promise')({})
const elasticsearch = require('elasticsearch')
const dbOptions = {
  host: process.env.AXIS_SQL_HOST,
  port: process.env.AXIS_SQL_PORT,
  database: process.env.AXIS_SQL_DBNAME,
  user: process.env.AXIS_SQL_USERNAME,
  password: process.env.AXIS_SQL_PASSWORD,
}

const sqlClient = PostgresPromise(dbOptions)
const esClient = new elasticsearch.Client({
  host: `${process.env.AXIS_ES_HOST}:${process.env.AXIS_ES_PORT}`,
  log: 'trace',
})

sqlClient.any(`SELECT id, url, scrape_time_utc FROM xinwenlianbo;`, true)
  .then(data => {
    // Dedupe
    const urlList = data.map(node => node.url)
    const urlSet = new Set(urlList)

    for (let uniqueUrl of urlSet) {
      sqlClient.any(`SELECT * FROM xinwenlianbo WHERE url='${uniqueUrl}'`)
        .then(matches => {

          // Deduplication, leaving the most update one
          const newestRecord = matches.reduce((newestRecord, nextRecord) =>
            nextRecord.scrape_time_utc > newestRecord.scrape_time_utc
            ? nextRecord
            : newestRecord
          )

          esClient.create({
            index: 'xinwenlianbo',
            type: 'extract',
            body: Object.assign(newestRecord, {
              html: '',
            }),
          })
            .then(message => console.log(message))
            .catch(error => console.error(error))

          esClient.create({
            index: 'xinwenlianbo',
            type: 'raw',
            body: {
              url: newestRecord.url,
              html: newestRecord.html,
            }
          })
            .then(message => console.log(message))
            .catch(error => console.error(error))

        })
        .catch(error => console.error(error))
    }
  })
  .catch(error => console.error(error))
