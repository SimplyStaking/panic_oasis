import { NANO } from './constants';

function scaleToNano(num) {
  return (num * NANO).toFixed(3);
}

export default scaleToNano;