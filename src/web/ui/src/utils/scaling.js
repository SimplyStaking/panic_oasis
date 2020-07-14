import { NANO } from './constants';

function scaleToNano(num) {
  return (num * NANO).toFixed(3);
}

// Obtained from https://stackoverflow.com/questions/15900485/correct-way-to-convert-size-in-bytes-to-kb-mb-gb-in-javascript
function scaleFromBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';

  const quotient = 1024;
  const dp = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(quotient));

  return `${parseFloat((bytes / (quotient ** i)).toFixed(dp))} ${sizes[i]}`;
}

export { scaleToNano, scaleFromBytes };
