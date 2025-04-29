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
 *
 * @param {IStopLocation} stop
 * @returns {{stop: string, platform: IPlatform, time: Date}}
 */
function simpleStop(stop) {
    return {
        stop: stopDisplayName(stop),
        platform: stop.platform,
        time: stop.time,
    }
}

/**
 *
 * @param {INode} node
 * @returns {{line: string, direction: string, duration: number, mode: string, departure: {stop: string, platform: IPlatform, time: Date}, arrival: {stop: string, platform: IPlatform, time: Date}}}
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
 * @return {Array} - A simplified array of nodes, including line, direction, duration, mode title, and processed departure and arrival stops.
 */
function simpleNodes(nodes) {
    return nodes
        .filter(node => node.mode.name !== "Footpath" && node.mode.name !== "StairsUp")
        .map(simpleNode);
}

/**
 *
 * @param {ITrip} trip
 * @returns {{departure: {stop: string, platform: IPlatform, time: Date}, arrival: {stop: string, platform: IPlatform, time: Date}, duration: number, interchanges: number, nodes: Array}}
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
 *
 * @param {IRoute} routes
 * @returns {{origin: string, destination: string, trips: {departure: {stop: string, platform: IPlatform, time: Date}, arrival: {stop: string, platform: IPlatform, time: Date}, duration: *, interchanges: *, nodes: Array}[]}}
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
