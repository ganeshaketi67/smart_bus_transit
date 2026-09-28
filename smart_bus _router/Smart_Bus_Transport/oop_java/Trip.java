public class Trip {
    private final Route route;
    private final Bus bus;
    private final String departureTime;

    public Trip(Route route, Bus bus, String departureTime) {
        this.route = route;
        this.bus = bus;
        this.departureTime = departureTime;
    }

    public Route getRoute() {
        return route;
    }

    public Bus getBus() {
        return bus;
    }

    public String getDepartureTime() {
        return departureTime;
    }
}