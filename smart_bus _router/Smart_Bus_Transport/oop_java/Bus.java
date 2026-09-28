public class Bus {
    private final String registrationNumber;
    private final int capacity;

    public Bus(String registrationNumber, int capacity) {
        if (capacity <= 0) {
            throw new IllegalArgumentException("Capacity must be greater than zero");
        }
        this.registrationNumber = registrationNumber;
        this.capacity = capacity;
    }

    public String getRegistrationNumber() {
        return registrationNumber;
    }

    public int getCapacity() {
        return capacity;
    }
}