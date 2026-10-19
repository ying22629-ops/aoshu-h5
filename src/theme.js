export const TOPIC_COLORS = {
  calc: '#6366f1',
  number: '#0d9488',
  travel: '#ea580c',
  count: '#db2777',
  geometry: '#16a34a',
  logic: '#ca8a04',
}

export const topicColor = (id) => TOPIC_COLORS[id] ?? '#6366f1'
