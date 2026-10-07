from pathlib import Path
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui

def vertical_flow_download(input_file:str, download_folder:str, output_file_name:str):
    XML_FILE = str(Path(input_file).resolve())

    prefs = {
    "download.default_directory": download_folder,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    }
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://app.diagrams.net/")

        try:
            driver.find_element(
                By.XPATH,
                "//*[contains(text(),'Decide later')]"
            ).click()
        except:
            pass

        try:
            driver.find_element(
                By.XPATH,
                "//*[contains(text(),'Not now')]"
            ).click()
        except:
            pass

        try:
            driver.find_element(
                By.XPATH,
                "//*[contains(text(),'Create New Diagram')]"
            ).click()

            driver.find_element(
                By.XPATH,
                "//*[contains(text(),'Cancel')]"
            ).click()
        except:
            pass
        time.sleep(5)
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        print("Inputs:", len(inputs))

        print("File")
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[text()='File']")
            )
        ).click()

        print("Import from")
        import_from = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(),'Import from')]")
            )
        )

        ActionChains(driver).move_to_element(import_from).perform()

        print("Device")
        device = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(),'Device...')]")
            )
        )

        device.click()

        print("Procurando input file")

        file_input = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='file']")
            )
        )
        print(file_input.get_attribute("outerHTML"))

        print("Upload")
        file_input.send_keys(XML_FILE)
        time.sleep(5)
        pyautogui.press("esc")

        try:
            wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[contains(text(),'Replace')]")
                )
            ).click()
        except:
            pass

        print("Arrange")
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[text()='Arrange']")
            )
        ).click()

        print("Layout")
        layout = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(),'Layout')]")
            )
        )

        ActionChains(driver).move_to_element(layout).perform()

        print("Vertical Flow")
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(),'Vertical Flow...')]")
            )
        ).click()

        try:
            wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[contains(text(),'Apply')]")
                )
            ).click()
        except:
            pass

        print("File")
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[text()='File']")
            )
        ).click()

        print("Export as")
        export_as = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(),'Export as')]")
            )
        )
        

        ActionChains(driver).move_to_element(export_as).perform()

        print("SVG")
        sml = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(),'SVG...')]")
            )
        )
        sml.click()

        print("Export")
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[text()='Export']")
            )
        ).click()

        print("Change File Name")
        filename_input = driver.find_element(
            By.XPATH,
            "//input[@type='text' and contains(@value,'.svg')]"
            )
        filename_input.clear()
        filename_input.send_keys(output_file_name)
        print("Save")
        wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[text()='Save']")
            )
        ).click()

        print("Concluído")
        

    except Exception as e:
        print(e)

    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass