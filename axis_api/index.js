'use strict'
const http = require('http')
const url = require('url')
const querystring = require('querystring')
const PostgresPromise = require('pg-promise')({})

const PORT = 21000

const INITIAL_DATE = new Date(2002, 0, 1)

const dbOptions = {
  host: 'localhost',
  port: 5432,
  database: 'xinwenlianbo',
  user: 'scrapy',
  password: 'scrapy',
}

const db = PostgresPromise(dbOptions)

function formatDate(date) {
  const yearString = String(date.getFullYear())

  let monthString = String(date.getMonth() + 1)
  if (date.getMonth() < 9) {
    monthString = '0' + monthString
  }

  return `${yearString}-${monthString}-01`
}

const jsonServer = http.createServer((httpRequest, httpResponse) => {
  const httpQuery = querystring.parse(url.parse(httpRequest.url).query)

  const dates = []
  let date = INITIAL_DATE
  const now = Date.now()
  while (date.getTime() < now) {
    const nextDate = new Date(date.getTime())
    nextDate.setMonth(date.getMonth() + 1)
    dates.push({
      begin: formatDate(date),
      end: formatDate(nextDate),
    })
    date = nextDate
  }

  const occurenceCountQueries = dates.map(period => {
    const sqlQuery = `
      SELECT COUNT(*) FROM reports
      WHERE
        ((main_text LIKE '%${httpQuery.kw}%'
          OR
          title LIKE '%${httpQuery.kw}%'
         )
         AND
         pub_date >= '${period.begin}'
         AND
         pub_date < '${period.end}'
        );`
    return db.any(sqlQuery, true)
  })

  Promise.all(occurenceCountQueries)
         .then(counts => {
           return counts.map((sqlResult, index) => {
             return Object.assign({}, dates[index], {
               data: sqlResult[0],
             })
           })
         })
        .then(results => {
          httpResponse.writeHead(200, {
            'Content-Type': 'application/json',
          })
          httpResponse.end(JSON.stringify(results))
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

