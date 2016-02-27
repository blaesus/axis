'use strict'
const http = require('http')
const url = require('url')
const querystring = require('querystring')
const PostgresPromise = require('pg-promise')({})

const PORT = 21000

const INITIAL_DATA_YAER = 2002

const dbOptions = {
  host: 'localhost',
  port: 5432,
  database: 'xinwenlianbo',
  user: 'scrapy',
  password: 'scrapy',
}

const db = PostgresPromise(dbOptions)

const jsonServer = http.createServer((httpRequest, httpResponse) => {
  const httpQuery = querystring.parse(url.parse(httpRequest.url).query)

  const sqlQuery = `
    SELECT COUNT(*) FROM reports
    WHERE main_text LIKE '%${httpQuery.kw}%';
  `
  console.log(sqlQuery)

  db.any(sqlQuery, true)
    .then(data => {
      httpResponse.writeHead(200, {
        'Content-Type': 'application/json',
      })
      httpResponse.end(JSON.stringify(data))
    })
    .catch(error => {
      console.error(error)
      httpResponse.writeHead(500, {
        'Content-Type': 'application/json',
      })
      httpResponse.end(JSON.stringify({
        error: error,
      }))
    })
})

jsonServer.listen(PORT, () => {
  console.info(`Axis Json Serve running at ${PORT}`)
})

