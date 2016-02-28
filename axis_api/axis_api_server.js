'use strict'
const http = require('http')
const url = require('url')
const querystring = require('querystring')
const fetch = require('node-fetch')

const PORT = 21000

const INITIAL_DATE = new Date(2002, 0, 1)

function getResultPromise(options) {
  const target = options.target.replace('/', '')
  const keyword = options.keyword
  const interval = options.interval || 'month'

  if (target === 'xinwenlianbo') {
    return fetch(`http://${process.env.AXIS_ES_HOST}:${process.env.AXIS_ES_PORT}/xinwenlianbo/extract/_search?size=0`, {
      method: 'POST',
      body: JSON.stringify({
        query: {
          term: {
            main_text: keyword
          }
        },
        aggs: {
          counts: {
            date_histogram: {
              field: 'pub_date',
              interval: interval,
            },
          },
        },
      }),
    })
  } else {
    Promise.reject(`Unknwon target ${target}`)
  }
}

const jsonServer = http.createServer((httpRequest, httpResponse) => {
  const httpQuery = url.parse(httpRequest.url, true)
  console.log(httpQuery)
  const queryStrings = httpQuery.query

  getResultPromise({
    target: httpQuery.pathname,
    keyword: queryStrings.kw,
    interval: queryStrings.interval,
  })
    .then(response => response.json())
    .then(results => {
      httpResponse.writeHead(200, {
        'Content-Type': 'application/json',
      })
      httpResponse.end(JSON.stringify({
        total_count: results.hits.total,
        counts: results.aggregations.counts.buckets
                  .map(node => ({
                    start_date: node.key,
                    count: node.doc_count,
                  })),
      }))
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

