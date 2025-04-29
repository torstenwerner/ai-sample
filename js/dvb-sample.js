import dvb_package from "dvbjs";

const {findStop, route, INode, IPlatform, IRoute, IStopLocation, ITrip} = dvb_package;

/**
 * Generates and returns the display name for a stop by combining its name and city.
 *
 * @param {IStopLocation} stop
 * @returns {string}
 */
function stopDisplayName(stop) {
    return `${stop.name} ${stop.city}`;
}

/**
 * @typedef ISimpleStop
 * @property {string} stop
 * @property {IPlatform} platform
 * @property {Date} time
 */

/**
 * Processes the given stop and returns an object containing relevant stop details.
 *
 * @param {IStopLocation} stop
 * @returns {ISimpleStop}
 */
function simpleStop(stop) {
    return {
        stop: stopDisplayName(stop),
        platform: stop.platform,
        time: stop.time,
    }
}

/**
 * @typedef ISimpleNode
 * @property {string} line
 * @property {string} direction
 * @property {number} duration
 * @property {string} mode
 * @property {ISimpleStop} departure
 * @property {ISimpleStop} arrival
 */

/**
 * Transforms a given node object into a simplified representation.
 *
 * @param {INode} node
 * @returns {ISimpleNode}
 */
function simpleNode(node) {
    return {
        line: node.line,
        direction: node.direction,
        duration: node.duration,
        mode: node.mode.title,
        departure: simpleStop(node.departure),
        arrival: simpleStop(node.arrival),
    }
}

/**
 * Filters and transforms a list of nodes to a simpler structure, excluding specific modes such as "Footpath" and "StairsUp".
 *
 * @param {INode[]} nodes - An array of node objects, where each node contains route, mode, and stop details.
 * @return {ISimpleNode[]} - A simplified array of nodes, including line, direction, duration, mode title, and processed departure and arrival stops.
 */
function simpleNodes(nodes) {
    return nodes
        .filter(node => node.mode.name !== "Footpath" && node.mode.name !== "StairsUp")
        .map(simpleNode);
}

/**
 * @typedef ISimpleTrip
 * @property {ISimpleStop} departure
 * @property {ISimpleStop} arrival
 * @property {number} duration
 * @property {number} interchanges
 * @property {ISimpleNode[]} nodes
 */

/**
 * Calculates as simplified trip.
 *
 * @param {ITrip} trip
 * @returns {ISimpleTrip}
 */
function simpleTrip(trip) {
    return {
        departure: simpleStop(trip.departure),
        arrival: simpleStop(trip.arrival),
        duration: trip.duration,
        interchanges: trip.interchanges,
        nodes: simpleNodes(trip.nodes),
    };
}

/**
 * @typedef ISimpleRoute
 * @property {string} origin
 * @property {string} destination
 * @property {ISimpleTrip[]} trips
 */

/**
 * Calculates a simplified route.
 *
 * @param {IRoute} route
 * @returns {ISimpleRoute}
 */
function simpleRoute(route) {
    return {
        origin: `${route.origin.name} ${route.origin.city}`,
        destination: `${route.destination.name} ${route.destination.city}`,
        trips: route.trips.map(simpleTrip),
    };
}

const origin = (await findStop("Königheim Dresden"))[0];
const destination = (await findStop("Riesa Bahnhof"))[0];

const startTime = new Date();
const isArrivalTime = false;

const rawRoute = await route(origin.id, destination.id, startTime, isArrivalTime);

console.dir(simpleRoute(rawRoute), {depth: 7, maxArrayLength: 10});
