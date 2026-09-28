import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Scheduler {
    private final List<Trip> trips = new ArrayList<>();

    public void addTrip(Trip trip) {
        trips.add(trip);
    }

    public List<Trip> getTrips() {
        return Collections.unmodifiableList(trips);
    }
}