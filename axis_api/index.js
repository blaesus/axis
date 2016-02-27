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

function getResultPromise(options) {
  const target = options.target.replace('/', '')
  const keyword = options.keyword
  const begin = options.begin
  const end = options.end
  console.info(options)

  if (target === 'xinwenlianbo') {
    const sqlQuery = `
      SELECT COUNT(*) FROM reports
      WHERE
      ((main_text LIKE '%${keyword}%'
      OR
      title LIKE '%${keyword}%'
      )
      AND
      pub_date >= '${begin}'
      AND
      pub_date < '${end}'
    );`
    return db.any(sqlQuery, true)
  } else {
    Promise.reject(`Unknwon target ${target}`)
  }
}

function formatDate(date) {
  const yearString = String(date.getFullYear())

  let monthString = String(date.getMonth() + 1)
  if (date.getMonth() < 9) {
    monthString = '0' + monthString
  }

  return `${yearString}-${monthString}-01`
}

const jsonServer = http.createServer((httpRequest, httpResponse) => {
  const httpQuery = url.parse(httpRequest.url)
  const queryStrings = querystring.parse(httpQuery.query)

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

  const occurrenceCountPromises = dates.map(period => getResultPromise({
    target: httpQuery.pathname,
    keyword: queryStrings.kw,
    begin: period.begin,
    end: period.end,
  }))

  Promise.all(occurrenceCountPromises)
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

