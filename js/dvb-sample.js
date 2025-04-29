import {findStop} from "dvbjs";

const stops = await findStop("Königheim Dresden");
console.dir({stop: stops}, {depth: 7, maxArrayLength: 2});
