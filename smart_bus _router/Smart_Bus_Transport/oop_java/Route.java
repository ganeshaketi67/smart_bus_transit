public class Route {
    private final String name;
    private final String origin;
    private final String destination;

    public Route(String name, String origin, String destination) {
        this.name = name;
        this.origin = origin;
        this.destination = destination;
    }

    public String getName() {
        return name;
    }

    public String getOrigin() {
        return origin;
    }

    public String getDestination() {
        return destination;
    }
}