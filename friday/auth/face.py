import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis


class FaceAuthenticator:
    """Interface placeholder for InsightFace-based authentication."""

    app = FaceAnalysis()
    app.prepare(ctx_id=0)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FACE_DB = os.path.join(BASE_DIR, "face_db")

    known_faces = {}

    for file in os.listdir(FACE_DB):
        if file.endswith(".npy"):
            name = os.path.splitext(file)[0]

            embedding = np.load(
                os.path.join(FACE_DB, file)
            )

            known_faces[name] = embedding

    print(f"Loaded {len(known_faces)} users.")


    def authenticate() -> list:

        THRESHOLD = 0.60

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Failed to open camera.")
            return False, None

        authenticated = False
        authenticated_user = None

        while True:

            ret, frame = cap.read()

            if not ret:
                print("Failed to read frame.")
                continue

            faces = FaceAuthenticator.app.get(frame)

            for face in faces:

                bbox = face.bbox.astype(int)
                current_embedding = face.embedding

                best_match = None
                best_similarity = -1

                # Compare against all users
                for name, stored_embedding in FaceAuthenticator.known_faces.items():

                    similarity = np.dot(
                        stored_embedding,
                        current_embedding
                    ) / (
                        np.linalg.norm(stored_embedding)
                        * np.linalg.norm(current_embedding)
                    )

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = name

                # Authentication Decision
                if best_similarity > THRESHOLD:

                    authenticated = True
                    authenticated_user = best_match

                    color = (0, 255, 0)
                    text = (
                        f"{best_match} "
                        f"({best_similarity:.2f})"
                    )

                else:

                    color = (0, 0, 255)
                    text = (
                        f"Unknown "
                        f"({best_similarity:.2f})"
                    )

                # Draw Bounding Box
                cv2.rectangle(
                    frame,
                    (bbox[0], bbox[1]),
                    (bbox[2], bbox[3]),
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    text,
                    (bbox[0], bbox[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

            cv2.imshow(
                "Face Authentication",
                frame
            )

            key = cv2.waitKey(1)

            # ESC key
            if key == 27:
                break

            # Stop after successful authentication
            if authenticated:
                print(
                    f"Authenticated: "
                    f"{authenticated_user}"
                )
                break
            
        cap.release()
        cv2.destroyAllWindows()
        
        return_list = [authenticated, authenticated_user]
        return return_list

    if __name__ == "__main__":
        authenticate()
