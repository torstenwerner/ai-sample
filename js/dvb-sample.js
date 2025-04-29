import dvb_package from "dvbjs";

const {findStop, route, INode, IPlatform, IRoute, IStopLocation, ITrip} = dvb_package;

/**
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
 *
 * @param {IRoute} routes
 * @returns {ISimpleRoute}
 */
function simpleRoutes(routes) {
    return {
        origin: `${routes.origin.name} ${routes.origin.city}`,
        destination: `${routes.destination.name} ${routes.destination.city}`,
        trips: routes.trips.map(simpleTrip),
    };
}

const origin = (await findStop("Königheim Dresden"))[0];
const destination = (await findStop("Riesa Bahnhof"))[0];

const startTime = new Date();
const isArrivalTime = false;

const routes = await route(origin.id, destination.id, startTime, isArrivalTime);

console.dir(simpleRoutes(routes), {depth: 7, maxArrayLength: 10});
