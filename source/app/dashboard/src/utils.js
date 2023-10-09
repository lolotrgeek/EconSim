
export function parse(data) {
    try {
      if (typeof data === 'object') return data
      const parsed = JSON.parse(data);
      if (typeof parsed === 'object') return parsed
      if (typeof parsed === 'string') {
        const re_parsed = JSON.parse(parsed)
        if (typeof re_parsed === 'object') return re_parsed
        const parsed_stringify = JSON.parse(JSON.stringify(data))
        if (typeof parsed_stringify === 'object') return parsed_stringify
        const escaped_string = data.replace(/(?:\\[n])+/g, '').replaceAll(/\s/g,'')
        const escape_parsed = JSON.parse(escaped_string)
        if (typeof escape_parsed === 'object') return escape_parsed
        else return { error: 'Unable to parse data'}
      }
    } catch (error) {
      return error;
    }
  }
